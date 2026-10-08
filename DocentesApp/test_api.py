from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APITestCase

from EstudiantesApp.models import Estudiante, Nota
from .models import Docente


class DocentesApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)
        cls.docente = Docente.objects.get(usuario__username='docente')

    def ingresar(self, usuario):
        cache.clear()
        respuesta = self.client.post(
            reverse('token'), {'username': usuario, 'password': 'Colegio2026!'}
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.json()['access']}")

    def datos_validos(self, **cambios):
        datos = {
            'nombre': 'Claudia Silva', 'rut': '17.123.456-7',
            'cuenta': 'claudia.silva@example.com',
        }
        datos.update(cambios)
        return datos

    def test_sin_token_responde_401(self):
        self.assertEqual(self.client.get(reverse('api-docentes-list')).status_code, 401)

    def test_administrador_ve_campos_sensibles_y_otros_perfiles_no(self):
        self.ingresar('admin')
        respuesta = self.client.get(reverse('api-docentes-detail', args=[self.docente.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue({'rut', 'cuenta', 'usuario'} <= set(respuesta.json()))

        self.ingresar('docente')
        respuesta = self.client.get(reverse('api-docentes-detail', args=[self.docente.pk]))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse({'rut', 'cuenta', 'usuario'} & set(respuesta.json()))

    def test_perfil_sin_permiso_recibe_403(self):
        self.ingresar('estudiante')
        respuesta = self.client.get(reverse('api-docentes-list'))
        self.assertEqual(respuesta.status_code, 403)
        respuesta = self.client.post(reverse('api-docentes-list'), self.datos_validos())
        self.assertEqual(respuesta.status_code, 403)

    def test_administrativo_crea_modifica_y_administrador_elimina(self):
        self.ingresar('administrativo')
        respuesta = self.client.post(reverse('api-docentes-list'), self.datos_validos())
        self.assertEqual(respuesta.status_code, 201)
        docente = Docente.objects.get(cuenta='claudia.silva@example.com')
        respuesta = self.client.put(
            reverse('api-docentes-detail', args=[docente.pk]),
            self.datos_validos(nombre='Claudia Silva Editada'),
        )
        self.assertEqual(respuesta.status_code, 200)

        self.ingresar('admin')
        respuesta = self.client.delete(reverse('api-docentes-detail', args=[docente.pk]))
        self.assertEqual(respuesta.status_code, 200)

    def test_datos_invalidos_y_registro_inexistente(self):
        self.ingresar('admin')
        respuesta = self.client.post(reverse('api-docentes-list'), self.datos_validos(nombre=' X '))
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('nombre', respuesta.json()['detalle'])
        respuesta = self.client.get(reverse('api-docentes-detail', args=[999999]))
        self.assertEqual(respuesta.status_code, 404)


class NotasApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)
        call_command('loaddata', 'estudiantes', verbosity=0)
        cls.usuario_docente = User.objects.get(username='docente')
        cls.docente = Docente.objects.get(usuario=cls.usuario_docente)
        cls.otro_usuario_docente = User.objects.create_user('docente2', password='ClaveEva2026!')
        cls.otro_usuario_docente.groups.add(Group.objects.get(name='Docente'))
        cls.otro_docente = Docente.objects.create(
            nombre='Docente Dos', cuenta='docente2@example.com',
            rut='18.123.456-8', usuario=cls.otro_usuario_docente,
        )
        cls.estudiante = Estudiante.objects.get(usuario__username='estudiante')
        cls.otro_estudiante_usuario = User.objects.create_user('estudiante2', password='ClaveEva2026!')
        cls.otro_estudiante_usuario.groups.add(Group.objects.get(name='Estudiante'))
        cls.otro_estudiante = Estudiante.objects.create(
            nombre='Estudiante Dos', rut='19.123.456-9', curso='2 Medio',
            cuenta='estudiante2@example.com', usuario=cls.otro_estudiante_usuario,
        )
        cls.nota = Nota.objects.create(
            estudiante=cls.estudiante, docente=cls.docente, asignatura='Historia',
            evaluacion='Prueba 1', calificacion=Decimal('6.0'),
        )
        cls.otra_nota = Nota.objects.create(
            estudiante=cls.otro_estudiante, docente=cls.otro_docente, asignatura='Ciencias',
            evaluacion='Prueba 2', calificacion=Decimal('5.5'),
        )

    def ingresar(self, usuario, password='Colegio2026!'):
        cache.clear()
        respuesta = self.client.post(reverse('token'), {'username': usuario, 'password': password})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {respuesta.json()['access']}")

    def test_estudiante_solo_ve_sus_notas_y_no_accede_a_detalle_ajeno(self):
        self.ingresar('estudiante')
        respuesta = self.client.get(reverse('api-notas-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([nota['id'] for nota in respuesta.json()['results']], [self.nota.pk])
        respuesta = self.client.get(reverse('api-notas-detail', args=[self.otra_nota.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_docente_solo_ve_notas_que_registro(self):
        self.ingresar('docente')
        respuesta = self.client.get(reverse('api-notas-list'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([nota['id'] for nota in respuesta.json()['results']], [self.nota.pk])
        respuesta = self.client.get(reverse('api-notas-detail', args=[self.otra_nota.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_administrador_y_administrativo_ven_todas_las_notas(self):
        for usuario in ('admin', 'administrativo'):
            with self.subTest(usuario=usuario):
                self.ingresar(usuario)
                respuesta = self.client.get(reverse('api-notas-list'))
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()['count'], 2)

    def test_docente_crea_nota_con_su_ficha_ignorando_docente_enviado(self):
        self.ingresar('docente')
        respuesta = self.client.post(reverse('api-notas-list'), {
            'estudiante': self.otro_estudiante.pk,
            'docente': self.otro_docente.pk,
            'asignatura': 'Matemáticas', 'evaluacion': 'Control', 'calificacion': '6.5',
        })
        self.assertEqual(respuesta.status_code, 201)
        creada = Nota.objects.get(pk=respuesta.json()['id'])
        self.assertEqual(creada.docente, self.docente)
        self.assertEqual(creada.estudiante, self.otro_estudiante)

    def test_estudiante_no_puede_modificar_ni_eliminar_notas(self):
        self.ingresar('estudiante')
        url = reverse('api-notas-detail', args=[self.nota.pk])
        datos = {
            'estudiante': self.estudiante.pk, 'asignatura': 'Historia',
            'evaluacion': 'Prueba 1', 'calificacion': '6.0',
        }
        self.assertEqual(self.client.put(url, datos).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_docente_puede_modificar_y_eliminar_solo_su_nota(self):
        self.ingresar('docente')
        datos = {
            'estudiante': self.estudiante.pk, 'asignatura': 'Historia',
            'evaluacion': 'Prueba editada', 'calificacion': '6.4',
        }
        respuesta = self.client.put(reverse('api-notas-detail', args=[self.nota.pk]), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            self.client.delete(reverse('api-notas-detail', args=[self.otra_nota.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.delete(reverse('api-notas-detail', args=[self.nota.pk])).status_code,
            200,
        )

    def test_calificacion_invalida_responde_400(self):
        self.ingresar('docente')
        respuesta = self.client.post(reverse('api-notas-list'), {
            'estudiante': self.estudiante.pk, 'asignatura': 'Historia',
            'evaluacion': 'Prueba', 'calificacion': '8.0',
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('calificacion', respuesta.json()['detalle'])
