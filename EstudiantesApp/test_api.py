import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Estudiante


MEDIA_TEMPORAL = tempfile.mkdtemp()

CAMPOS_SENSIBLES = {
    'rut',
    'cuenta',
    'ficha_matricula',
    'usuario',
}


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class EstudiantesApiTests(APITestCase):
    """CRUD de estudiantes por API: permisos y datos sensibles."""

    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)

        cls.estudiante = Estudiante.objects.create(
            nombre='Juan Pérez',
            rut='12345678-9',
            curso='4°A',
            cuenta='juan.perez@test.cl',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def ingresar(self, usuario):
        respuesta = self.client.post(
            reverse('token'),
            {
                'username': usuario,
                'password': 'Colegio2026!',
            },
        )

        self.assertEqual(respuesta.status_code, 200)

        access = respuesta.json()['access']
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {access}'
        )

    def url_detalle(self, estudiante=None):
        estudiante = estudiante or self.estudiante
        return reverse(
            'api-estudiantes-detail',
            args=[estudiante.pk],
        )

    def datos_validos(self, **cambios):
        datos = {
            'nombre': 'María González',
            'rut': '98765432-1',
            'curso': '3°B',
            'cuenta': 'maria.gonzalez@test.cl',
        }
        datos.update(cambios)
        return datos

    # -------------------------------------------------------------------------
    # Lectura y autenticación
    # -------------------------------------------------------------------------

    def test_sin_token_responde_401(self):
        respuesta = self.client.get(
            reverse('api-estudiantes-list')
        )

        self.assertEqual(respuesta.status_code, 401)

    def test_administrador_ve_campos_sensibles(self):
        self.ingresar('admin')

        respuesta = self.client.get(self.url_detalle())

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(
            CAMPOS_SENSIBLES <= set(respuesta.json())
        )

        self.assertEqual(
            respuesta.json()['rut'],
            '12345678-9',
        )

    def test_administrativo_no_ve_campos_sensibles(self):
        self.ingresar('administrativo')

        respuesta = self.client.get(
            reverse('api-estudiantes-list')
        )

        self.assertEqual(respuesta.status_code, 200)

        estudiante = respuesta.json()['results'][0]

        self.assertFalse(
            CAMPOS_SENSIBLES & set(estudiante)
        )

        self.assertIn('nombre', estudiante)
        self.assertIn('curso', estudiante)

    def test_docente_no_ve_campos_sensibles(self):
        self.ingresar('docente')

        respuesta = self.client.get(
            reverse('api-estudiantes-list')
        )

        self.assertEqual(respuesta.status_code, 200)

        estudiante = respuesta.json()['results'][0]

        self.assertFalse(
            CAMPOS_SENSIBLES & set(estudiante)
        )

        self.assertIn('nombre', estudiante)
        self.assertIn('curso', estudiante)

    def test_estudiante_no_puede_consultar_estudiantes(self):
        self.ingresar('estudiante')

        respuesta = self.client.get(
            reverse('api-estudiantes-list')
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_estudiante_inexistente_responde_404(self):
        self.ingresar('admin')

        respuesta = self.client.get(
            reverse(
                'api-estudiantes-detail',
                args=[9999],
            )
        )

        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(
            respuesta.json()['codigo'],
            404,
        )

    # -------------------------------------------------------------------------
    # Búsqueda
    # -------------------------------------------------------------------------

    def test_listado_paginado_con_busqueda(self):
        self.ingresar('docente')

        respuesta = self.client.get(
            reverse('api-estudiantes-list'),
            {'search': 'Juan'},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['count'], 1)
        self.assertEqual(
            respuesta.json()['results'][0]['nombre'],
            'Juan Pérez',
        )

    def test_no_se_puede_buscar_por_datos_sensibles(self):
        self.ingresar('docente')

        respuesta = self.client.get(
            reverse('api-estudiantes-list'),
            {'search': '12345678-9'},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['count'], 0)

    # -------------------------------------------------------------------------
    # Crear
    # -------------------------------------------------------------------------

    def test_administrativo_crea_estudiante_y_recibe_201(self):
        self.ingresar('administrativo')

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 201)

        estudiante = Estudiante.objects.get(
            rut='98765432-1'
        )

        self.assertEqual(
            estudiante.nombre,
            'María González',
        )

        self.assertFalse(
            CAMPOS_SENSIBLES & set(respuesta.json())
        )

    def test_docente_no_puede_crear_estudiante(self):
        self.ingresar('docente')

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_estudiante_no_puede_crear_estudiante(self):
        self.ingresar('estudiante')

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            self.datos_validos(),
        )

        self.assertEqual(respuesta.status_code, 403)

    # -------------------------------------------------------------------------
    # Modificar
    # -------------------------------------------------------------------------

    def test_administrativo_modifica_estudiante_y_recibe_200(self):
        self.ingresar('administrativo')

        datos = self.datos_validos(
            nombre='Juan Pérez Modificado',
            rut='12345678-9',
            cuenta='juan.perez@test.cl',
        )

        respuesta = self.client.put(
            self.url_detalle(),
            datos,
        )

        self.assertEqual(respuesta.status_code, 200)

        self.estudiante.refresh_from_db()

        self.assertEqual(
            self.estudiante.nombre,
            'Juan Pérez Modificado',
        )

    def test_docente_no_puede_modificar_estudiante(self):
        self.ingresar('docente')

        datos = self.datos_validos(
            rut='12345678-9',
            cuenta='juan.perez@test.cl',
        )

        respuesta = self.client.put(
            self.url_detalle(),
            datos,
        )

        self.assertEqual(respuesta.status_code, 403)

    # -------------------------------------------------------------------------
    # Datos inválidos
    # -------------------------------------------------------------------------

    def test_nombre_invalido_responde_400_con_detalle(self):
        self.ingresar('administrativo')

        datos = self.datos_validos(
            nombre='A',
        )

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            datos,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json()['codigo'],
            400,
        )
        self.assertIn(
            'nombre',
            respuesta.json()['detalle'],
        )

    def test_curso_vacio_responde_400_con_detalle(self):
        self.ingresar('administrativo')

        datos = self.datos_validos(
            curso='',
        )

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            datos,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json()['codigo'],
            400,
        )
        self.assertIn(
            'curso',
            respuesta.json()['detalle'],
        )

    def test_rut_duplicado_responde_400(self):
        self.ingresar('administrativo')

        datos = self.datos_validos(
            rut='12345678-9',
            cuenta='otro.estudiante@test.cl',
        )

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            datos,
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json()['codigo'],
            400,
        )

    # -------------------------------------------------------------------------
    # Eliminar
    # -------------------------------------------------------------------------

    def test_docente_no_puede_eliminar_estudiante(self):
        self.ingresar('docente')

        respuesta = self.client.delete(
            self.url_detalle()
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_administrativo_no_puede_eliminar_estudiante(self):
        self.ingresar('administrativo')

        respuesta = self.client.delete(
            self.url_detalle()
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_elimina_estudiante_y_recibe_200(self):
        self.ingresar('admin')

        respuesta = self.client.delete(
            self.url_detalle()
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            'mensaje',
            respuesta.json(),
        )

        self.assertFalse(
            Estudiante.objects.filter(
                pk=self.estudiante.pk
            ).exists()
        )

    # -------------------------------------------------------------------------
    # Métodos no permitidos
    # -------------------------------------------------------------------------

    def test_patch_no_esta_permitido(self):
        self.ingresar('administrativo')

        respuesta = self.client.patch(
            self.url_detalle(),
            {'nombre': 'Cambio'},
        )

        self.assertEqual(respuesta.status_code, 405)

    # -------------------------------------------------------------------------
    # Archivos
    # -------------------------------------------------------------------------

    def test_ficha_matricula_debe_ser_pdf(self):
        self.ingresar('administrativo')

        archivo = SimpleUploadedFile(
            'ficha.txt',
            b'contenido de prueba',
            content_type='text/plain',
        )

        datos = self.datos_validos(
            ficha_matricula=archivo,
        )

        respuesta = self.client.post(
            reverse('api-estudiantes-list'),
            datos,
            format='multipart',
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            respuesta.json()['codigo'],
            400,
        )