import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Administrativo

MEDIA_TEMPORAL = tempfile.mkdtemp()
CAMPOS_SENSIBLES = {'correo_electronico', 'telefono', 'fecha_contratacion', 'contrato', 'usuario'}


class AutenticacionJWTTests(APITestCase):
    """Base de la API: tokens JWT, endpoint protegido y Swagger."""

    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)

    def setUp(self):
        # El límite de intentos se guarda en caché: se limpia entre pruebas.
        cache.clear()

    def obtener_tokens(self, usuario='docente', clave='Colegio2026!'):
        return self.client.post(reverse('token'), {'username': usuario, 'password': clave})

    def test_obtiene_access_y_refresh(self):
        respuesta = self.obtener_tokens()
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.json())
        self.assertIn('refresh', respuesta.json())

    def test_obtiene_token_con_correo(self):
        respuesta = self.obtener_tokens('docente@colegiodigital.cl')
        self.assertEqual(respuesta.status_code, 200)

    def test_credenciales_invalidas_responden_401(self):
        respuesta = self.obtener_tokens(clave='incorrecta')
        self.assertEqual(respuesta.status_code, 401)
        self.assertEqual(respuesta['Content-Type'], 'application/json')
        self.assertEqual(respuesta.json()['codigo'], 401)
        self.assertIn('error', respuesta.json())

    def test_error_sin_token_tiene_formato_uniforme(self):
        cuerpo = self.client.get(reverse('mi_perfil')).json()
        self.assertEqual(cuerpo['codigo'], 401)
        self.assertTrue(cuerpo['error'])

    def test_datos_incompletos_responden_400_con_detalle(self):
        respuesta = self.client.post(reverse('token'), {'username': 'docente'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()['codigo'], 400)
        self.assertIn('password', respuesta.json()['detalle'])

    def test_ruta_inexistente_de_la_api_responde_404_en_json(self):
        respuesta = self.client.get('/api/no-existe/')
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()['codigo'], 404)

    def test_limita_intentos_de_login(self):
        for _ in range(10):
            self.obtener_tokens(clave='incorrecta')
        respuesta = self.obtener_tokens(clave='incorrecta')
        self.assertEqual(respuesta.status_code, 429)
        self.assertEqual(respuesta.json()['codigo'], 429)

    def test_endpoint_protegido_sin_token_responde_401(self):
        respuesta = self.client.get(reverse('mi_perfil'))
        self.assertEqual(respuesta.status_code, 401)

    def test_endpoint_protegido_con_token_invalido_responde_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token-falso')
        self.assertEqual(self.client.get(reverse('mi_perfil')).status_code, 401)

    def test_endpoint_protegido_con_token_responde_datos_del_usuario(self):
        access = self.obtener_tokens().json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        respuesta = self.client.get(reverse('mi_perfil'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json(), {
            'usuario': 'docente', 'nombre': 'María Pérez', 'perfil': 'docente',
        })

    def test_refresh_entrega_nuevo_access_y_no_se_puede_reutilizar(self):
        refresh = self.obtener_tokens().json()['refresh']

        respuesta = self.client.post(reverse('token_refresh'), {'refresh': refresh})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('access', respuesta.json())
        self.assertIn('refresh', respuesta.json())

        # Rotación: el refresh ya usado queda en la lista negra.
        repetido = self.client.post(reverse('token_refresh'), {'refresh': refresh})
        self.assertEqual(repetido.status_code, 401)

    def test_swagger_y_esquema_disponibles(self):
        self.assertEqual(self.client.get(reverse('swagger')).status_code, 200)
        esquema = self.client.get(reverse('schema'))
        self.assertEqual(esquema.status_code, 200)
        self.assertIn(b'/api/token/', esquema.content)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class AdministrativosApiTests(APITestCase):
    """CRUD de funcionarios por API: permisos por perfil y datos sensibles."""

    fixtures = ['funcionarios']

    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)
        cls.marcela = Administrativo.objects.get(nombre='Marcela')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def ingresar(self, usuario):
        access = self.client.post(
            reverse('token'), {'username': usuario, 'password': 'Colegio2026!'}
        ).json()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def url_detalle(self, funcionario=None):
        return reverse('api-administrativos-detail', args=[(funcionario or self.marcela).pk])

    def datos_validos(self, **cambios):
        datos = {
            'nombre': 'Rodrigo', 'apellido': 'Díaz', 'cargo': 'Secretario',
            'departamento': 'Secretaría', 'correo_electronico': 'rodrigo.diaz@colegiodigital.cl',
            'telefono': '+56 9 8765 4321',
        }
        datos.update(cambios)
        return datos

    # --- Lectura y datos sensibles -------------------------------------------------

    def test_sin_token_responde_401(self):
        self.assertEqual(self.client.get(reverse('api-administrativos-list')).status_code, 401)

    def test_administrador_ve_campos_sensibles(self):
        self.ingresar('admin')
        respuesta = self.client.get(self.url_detalle())
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(CAMPOS_SENSIBLES <= set(respuesta.json()))
        self.assertEqual(respuesta.json()['correo_electronico'], 'marcela.rojas@colegiodigital.cl')

    def test_otros_perfiles_no_ven_campos_sensibles(self):
        for usuario in ['administrativo', 'docente', 'estudiante']:
            with self.subTest(usuario=usuario):
                self.ingresar(usuario)
                respuesta = self.client.get(reverse('api-administrativos-list'))
                self.assertEqual(respuesta.status_code, 200)
                funcionario = respuesta.json()['results'][0]
                self.assertFalse(CAMPOS_SENSIBLES & set(funcionario))
                self.assertIn('nombre', funcionario)

    def test_listado_paginado_con_busqueda(self):
        self.ingresar('docente')
        respuesta = self.client.get(reverse('api-administrativos-list'), {'search': 'directora'})
        self.assertEqual(respuesta.json()['count'], 1)
        self.assertEqual(respuesta.json()['results'][0]['nombre'], 'Marcela')

    def test_no_se_puede_buscar_por_datos_sensibles(self):
        self.ingresar('administrativo')
        respuesta = self.client.get(
            reverse('api-administrativos-list'), {'search': 'marcela.rojas@colegiodigital.cl'}
        )
        self.assertEqual(respuesta.json()['count'], 0)

    def test_funcionario_inexistente_responde_404(self):
        self.ingresar('admin')
        respuesta = self.client.get(reverse('api-administrativos-detail', args=[9999]))
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()['codigo'], 404)

    # --- Crear y modificar ---------------------------------------------------------

    def test_administrativo_crea_y_recibe_201_sin_datos_sensibles(self):
        self.ingresar('administrativo')
        respuesta = self.client.post(reverse('api-administrativos-list'), self.datos_validos())
        self.assertEqual(respuesta.status_code, 201)
        self.assertFalse(CAMPOS_SENSIBLES & set(respuesta.json()))
        creado = Administrativo.objects.get(apellido='Díaz')
        self.assertEqual(creado.correo_electronico, 'rodrigo.diaz@colegiodigital.cl')

    def test_docente_no_puede_crear(self):
        self.ingresar('docente')
        respuesta = self.client.post(reverse('api-administrativos-list'), self.datos_validos())
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn('docente', respuesta.json()['error'])

    def test_administrativo_modifica_con_put(self):
        self.ingresar('administrativo')
        datos = self.datos_validos(
            nombre='Marcela', apellido='Rojas', correo_electronico=self.marcela.correo_electronico,
            cargo='Directora General',
        )
        respuesta = self.client.put(self.url_detalle(), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.marcela.refresh_from_db()
        self.assertEqual(self.marcela.cargo, 'Directora General')

    def test_datos_invalidos_responden_400_con_detalle(self):
        self.ingresar('admin')
        respuesta = self.client.post(
            reverse('api-administrativos-list'), self.datos_validos(telefono='abc', nombre='')
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('telefono', respuesta.json()['detalle'])
        self.assertIn('nombre', respuesta.json()['detalle'])

    def test_correo_repetido_responde_400(self):
        self.ingresar('admin')
        respuesta = self.client.post(
            reverse('api-administrativos-list'),
            self.datos_validos(correo_electronico='MARCELA.ROJAS@colegiodigital.cl'),
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('correo_electronico', respuesta.json()['detalle'])

    def test_contrato_debe_ser_pdf(self):
        self.ingresar('admin')
        datos = self.datos_validos(contrato=SimpleUploadedFile('contrato.exe', b'MZ'))
        respuesta = self.client.post(reverse('api-administrativos-list'), datos, format='multipart')
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('contrato', respuesta.json()['detalle'])

    def test_contrato_no_puede_superar_5_mb(self):
        self.ingresar('admin')
        grande = SimpleUploadedFile('contrato.pdf', b'0' * (5 * 1024 * 1024 + 1))
        respuesta = self.client.post(
            reverse('api-administrativos-list'), self.datos_validos(contrato=grande),
            format='multipart',
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn('5 MB', str(respuesta.json()['detalle']))

    # --- Eliminar ------------------------------------------------------------------

    def test_solo_el_administrador_elimina(self):
        self.ingresar('administrativo')
        self.assertEqual(self.client.delete(self.url_detalle()).status_code, 403)
        self.assertTrue(Administrativo.objects.filter(pk=self.marcela.pk).exists())

        self.ingresar('admin')
        respuesta = self.client.delete(self.url_detalle())
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('eliminado correctamente', respuesta.json()['mensaje'])
        self.assertEqual(self.client.get(self.url_detalle()).status_code, 404)

    def test_patch_no_esta_disponible(self):
        self.ingresar('admin')
        respuesta = self.client.patch(self.url_detalle(), {'cargo': 'X'})
        self.assertEqual(respuesta.status_code, 405)
