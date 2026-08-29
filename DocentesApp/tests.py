from django.test import TestCase
from django.urls import reverse


class DocentesViewsTests(TestCase):
    def test_login_docente_renderiza_la_base_compartida(self):
        respuesta = self.client.get(reverse("login"))

        self.assertContains(respuesta, "Colegio Digital")
        self.assertContains(respuesta, "Área de Docentes")

    def test_docente_puede_iniciar_sesion_y_ver_panel(self):
        respuesta = self.client.post(
            reverse("login"),
            {"cuenta": "ejemplo@demo.cl", "rut": "12345678-9"},
        )

        self.assertRedirects(respuesta, reverse("listado_docentes"))
        self.assertContains(self.client.get(reverse("listado_docentes")), "Panel de información académica")
