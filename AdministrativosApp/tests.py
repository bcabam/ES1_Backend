from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch


class AdministrativosViewsTests(TestCase):
    def test_vistas_administrativas_requieren_rol(self):
        self.assertRedirects(
            self.client.get(reverse("administrativos:inicio")),
            reverse("administrativos:login"),
        )
        self.assertRedirects(
            self.client.get(reverse("administrativos:registro")),
            reverse("administrativos:login"),
        )

    @patch("AdministrativosApp.views.check_password", return_value=True)
    def test_administrativo_no_puede_acceder_a_otra_area(self, _check_password):
        respuesta_login = self.client.post(
            reverse("administrativos:login"),
            {"correo": "administrativos@colegiodigital.cl", "contrasena": "secreto"},
        )

        self.assertRedirects(respuesta_login, reverse("administrativos:inicio"))
        respuesta_inicio = self.client.get(reverse("administrativos:inicio"))
        self.assertContains(respuesta_inicio, "Área Administrativa")
        self.assertRedirects(self.client.get(reverse("login")), reverse("administrativos:inicio"))
