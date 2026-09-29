from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse


class DocentesViewsTests(TestCase):
    def setUp(self):
        docente = User.objects.create_user("docente", password="Colegio2026!")
        docente.groups.add(Group.objects.create(name="Docente"))
        self.client.force_login(docente)

    def test_docente_puede_ver_su_panel(self):
        respuesta = self.client.get(reverse("listado_docentes"))

        self.assertContains(respuesta, "Colegio Digital")
        self.assertContains(respuesta, "Panel de información académica")

    def test_docente_no_puede_abrir_areas_de_otro_rol(self):
        destino = reverse("inicio_por_perfil")
        self.assertRedirects(
            self.client.get(reverse("estudiantes:notas")), destino,
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.get(reverse("administrativos:inicio")), destino,
            fetch_redirect_response=False,
        )
