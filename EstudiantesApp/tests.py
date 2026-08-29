from django.test import TestCase
from django.urls import reverse


class LoginEstudianteTests(TestCase):
    def test_estudiante_puede_iniciar_sesion_y_ver_notas(self):
        respuesta = self.client.post(
            reverse("estudiantes:login"),
            {"correo": "ESTUDIANTES@COLEGIODIGITAL.CL", "password": "123456"},
        )

        self.assertRedirects(respuesta, reverse("estudiantes:notas"))
        respuesta = self.client.get(reverse("estudiantes:notas"))
        self.assertContains(respuesta, "Juan Alcachofa")
        self.assertContains(respuesta, "Matemática")

    def test_credenciales_invalidas_muestran_error(self):
        respuesta = self.client.post(
            reverse("estudiantes:login"),
            {"correo": "estudiantes@colegiodigital.cl", "password": "incorrecta"},
        )

        self.assertContains(respuesta, "Correo o contraseña incorrectos.")

    def test_notas_requiere_sesion(self):
        respuesta = self.client.get(reverse("estudiantes:notas"))

        self.assertRedirects(respuesta, reverse("estudiantes:login"))

    def test_cerrar_sesion_elimina_la_sesion(self):
        self.client.post(
            reverse("estudiantes:login"),
            {"correo": "estudiantes@colegiodigital.cl", "password": "123456"},
        )

        respuesta = self.client.post(reverse("estudiantes:logout"))

        self.assertRedirects(respuesta, reverse("estudiantes:login"))
        self.assertNotIn("usuario_id", self.client.session)

    def test_estudiante_no_puede_abrir_areas_de_docentes_o_administrativos(self):
        self.client.post(
            reverse("estudiantes:login"),
            {"correo": "estudiantes@colegiodigital.cl", "password": "123456"},
        )

        destino = reverse("estudiantes:notas")
        self.assertRedirects(self.client.get(reverse("listado_docentes")), destino)
        self.assertRedirects(
            self.client.get(reverse("administrativos:inicio")), destino
        )
        self.assertRedirects(self.client.get(reverse("login")), destino)
