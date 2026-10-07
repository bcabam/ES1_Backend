from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase


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
