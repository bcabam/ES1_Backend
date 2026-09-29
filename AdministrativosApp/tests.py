from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class LoginUnicoTests(TestCase):
    """Prueba el login único y que cada perfil llegue solo a su área."""

    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)

    def ingresar(self, usuario):
        return self.client.post(
            reverse('login'), {'username': usuario, 'password': 'Colegio2026!'}
        )

    def test_vistas_protegidas_piden_login(self):
        respuesta = self.client.get(reverse('administrativos:inicio'))
        self.assertRedirects(
            respuesta, f"{reverse('login')}?next={reverse('administrativos:inicio')}"
        )

    def test_credenciales_invalidas_muestran_error(self):
        respuesta = self.client.post(
            reverse('login'), {'username': 'docente', 'password': 'incorrecta'}
        )
        self.assertContains(respuesta, 'Usuario o contraseña incorrectos.')

    def test_cada_perfil_llega_a_su_inicio(self):
        destinos = {
            'admin': reverse('administrativos:inicio'),
            'administrativo': reverse('administrativos:inicio'),
            'docente': reverse('listado_docentes'),
            'estudiante': reverse('estudiantes:notas'),
        }
        for usuario, destino in destinos.items():
            with self.subTest(usuario=usuario):
                self.ingresar(usuario)
                self.assertRedirects(
                    self.client.get(reverse('inicio_por_perfil')), destino,
                    fetch_redirect_response=False,
                )
                self.client.post(reverse('logout'))

    def test_estudiante_no_puede_entrar_a_otras_areas(self):
        self.ingresar('estudiante')
        for url in [reverse('administrativos:inicio'), reverse('listado_docentes'),
                    reverse('listar_docentes')]:
            with self.subTest(url=url):
                self.assertRedirects(
                    self.client.get(url), reverse('inicio_por_perfil'),
                    fetch_redirect_response=False,
                )

    def test_solo_el_administrador_crea_usuarios(self):
        self.ingresar('administrativo')
        self.assertRedirects(
            self.client.get(reverse('administrativos:crear_usuario')),
            reverse('inicio_por_perfil'), fetch_redirect_response=False,
        )
        self.client.post(reverse('logout'))

        self.ingresar('admin')
        self.client.post(reverse('administrativos:crear_usuario'), {
            'username': 'nuevo.docente', 'first_name': 'Nuevo', 'last_name': 'Docente',
            'email': 'nuevo@colegiodigital.cl', 'perfil': 'docente',
            'password1': 'ClaveSegura2026!', 'password2': 'ClaveSegura2026!',
        })
        nuevo = User.objects.get(username='nuevo.docente')
        self.assertTrue(nuevo.groups.filter(name='Docente').exists())

    def test_menu_cambia_segun_perfil(self):
        self.ingresar('estudiante')
        respuesta = self.client.get(reverse('estudiantes:notas'))
        self.assertContains(respuesta, 'Mis notas')
        self.assertNotContains(respuesta, 'Crear usuario')

    def test_logout_cierra_la_sesion(self):
        self.ingresar('docente')
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_usuario_sin_grupo_no_puede_ingresar(self):
        User.objects.create_user('sin_perfil', password='Colegio2026!')
        self.ingresar('sin_perfil')
        self.assertRedirects(
            self.client.get(reverse('inicio_por_perfil')), reverse('login')
        )
        self.assertFalse(Group.objects.filter(user__username='sin_perfil').exists())
