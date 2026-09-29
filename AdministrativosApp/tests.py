import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Administrativo


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


MEDIA_TEMPORAL = tempfile.mkdtemp()

# Imagen GIF de 1x1 píxel, suficiente para validar un ImageField.
GIF_MINIMO = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04'
    b'\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


@override_settings(MEDIA_ROOT=MEDIA_TEMPORAL)
class FuncionariosTests(TestCase):
    fixtures = ['funcionarios']

    @classmethod
    def setUpTestData(cls):
        call_command('crear_perfiles', '--demo', verbosity=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_TEMPORAL, ignore_errors=True)

    def setUp(self):
        self.client.login(username='administrativo', password='Colegio2026!')

    def test_lista_funcionarios_desde_la_base_de_datos(self):
        respuesta = self.client.get(reverse('administrativos:listar_funcionarios'))
        self.assertContains(respuesta, 'Marcela')
        self.assertEqual(respuesta.context['total_funcionarios'], 4)

    def test_busqueda_filtra_funcionarios(self):
        respuesta = self.client.get(
            reverse('administrativos:listar_funcionarios'), {'q': 'directora'}
        )
        self.assertEqual(respuesta.context['total_funcionarios'], 1)
        self.assertContains(respuesta, 'Marcela')

    def test_foto_y_contrato_se_muestran(self):
        funcionario = Administrativo.objects.get(nombre='Marcela')
        funcionario.foto = SimpleUploadedFile('foto.gif', GIF_MINIMO, content_type='image/gif')
        funcionario.contrato = SimpleUploadedFile(
            'contrato.pdf', b'%PDF-1.4 prueba', content_type='application/pdf'
        )
        funcionario.save()

        respuesta = self.client.get(reverse('administrativos:listar_funcionarios'))
        self.assertContains(respuesta, funcionario.foto.url)
        self.assertContains(respuesta, funcionario.contrato.url)

    def test_admin_sube_foto_y_contrato(self):
        self.client.login(username='admin', password='Colegio2026!')
        funcionario = Administrativo.objects.get(nombre='Marcela')
        url = reverse('admin:AdministrativosApp_administrativo_change', args=[funcionario.pk])
        self.client.post(url, {
            'nombre': funcionario.nombre, 'apellido': funcionario.apellido,
            'cargo': funcionario.cargo, 'departamento': funcionario.departamento,
            'correo_electronico': funcionario.correo_electronico,
            'telefono': funcionario.telefono,
            'foto': SimpleUploadedFile('foto.gif', GIF_MINIMO, content_type='image/gif'),
            'contrato': SimpleUploadedFile('contrato.pdf', b'%PDF-1.4', content_type='application/pdf'),
        })
        funcionario.refresh_from_db()
        self.assertTrue(funcionario.foto.name.startswith('administrativos/fotos/'))
        self.assertTrue(funcionario.contrato.name.startswith('administrativos/contratos/'))

    def test_contrato_debe_ser_pdf(self):
        funcionario = Administrativo.objects.get(nombre='Marcela')
        funcionario.contrato = SimpleUploadedFile('contrato.exe', b'MZ')
        with self.assertRaises(ValidationError):
            funcionario.full_clean()
