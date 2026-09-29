from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


class NotasEstudianteTests(TestCase):
    def setUp(self):
        self.estudiante = User.objects.create_user(
            "estudiante", password="Colegio2026!", first_name="Juan", last_name="Alcachofa"
        )
        self.estudiante.groups.add(Group.objects.create(name="Estudiante"))

    def test_estudiante_ve_sus_notas(self):
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse("estudiantes:notas"))

        self.assertContains(respuesta, "Juan Alcachofa")
        self.assertContains(respuesta, "Matemática")

    def test_notas_requiere_sesion(self):
        respuesta = self.client.get(reverse("estudiantes:notas"))

        self.assertRedirects(
            respuesta, f"{reverse('login')}?next={reverse('estudiantes:notas')}"
        )

    def test_estudiante_no_puede_abrir_areas_de_docentes_o_administrativos(self):
        self.client.force_login(self.estudiante)
        destino = reverse("inicio_por_perfil")

        self.assertRedirects(
            self.client.get(reverse("listado_docentes")), destino,
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.get(reverse("administrativos:inicio")), destino,
            fetch_redirect_response=False,
        )
