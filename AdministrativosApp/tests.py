from django.test import TestCase
from django.urls import reverse


class AdministrativosViewsTests(TestCase):
    def test_vistas_administrativas_estan_disponibles(self):
        respuesta_inicio = self.client.get(reverse("administrativos:inicio"))
        respuesta_login = self.client.get(reverse("administrativos:login"))
        respuesta_funcionarios = self.client.get(
            reverse("administrativos:listar_funcionarios")
        )

        self.assertContains(respuesta_inicio, "Área Administrativa")
        self.assertContains(respuesta_login, "Iniciar sesión")
        self.assertContains(respuesta_funcionarios, "Funcionarios")
