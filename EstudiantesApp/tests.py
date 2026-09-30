from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Estudiante, Nota


class NotasEstudianteTests(TestCase):
    def setUp(self):
        self.estudiante = User.objects.create_user(
            "estudiante", password="Colegio2026!", first_name="Juan", last_name="Alcachofa"
        )
        self.estudiante.groups.add(Group.objects.create(name="Estudiante"))

    def test_estudiante_ve_sus_notas(self):
        alumno = Estudiante.objects.create(
            nombre="Juan Alcachofa",
            rut="12.345.678-9",
            curso="1° Medio A",
            cuenta="juan.alcachofa@example.com",
            usuario=self.estudiante,
        )
        nota = Nota.objects.create(
            estudiante=alumno,
            docente=self.estudiante,
            asignatura="Ciencias",
            evaluacion="Evaluación diagnóstica",
            calificacion=Decimal("6.5"),
        )
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse("estudiantes:notas"))

        self.assertContains(respuesta, "Juan Alcachofa")
        self.assertContains(respuesta, nota.asignatura)
        self.assertContains(respuesta, nota.evaluacion)
        self.assertContains(respuesta, "6.5")

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


class CrudEstudiantesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", "--demo", verbosity=0)
        cls.estudiante = Estudiante.objects.create(
            nombre="Camila Rojas", rut="21.111.111-1",
            curso="4° Medio A", cuenta="camila.rojas@colegiodigital.cl",
        )

    def ingresar(self, usuario):
        self.client.login(username=usuario, password="Colegio2026!")

    def test_crud_requiere_sesion(self):
        url = reverse("estudiantes:lista_estudiantes")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_administrativo_lista_busca_y_crea(self):
        self.ingresar("administrativo")
        respuesta = self.client.get(
            reverse("estudiantes:lista_estudiantes"), {"busqueda": "Camila"}
        )
        self.assertContains(respuesta, "Camila Rojas")
        self.assertNotContains(respuesta, "Eliminar")

        self.client.post(reverse("estudiantes:crear_estudiante"), {
            "nombre": "Diego Pérez", "rut": "22.222.222-2",
            "curso": "4° Medio A", "cuenta": "diego.perez@colegiodigital.cl",
        })
        self.assertTrue(Estudiante.objects.filter(rut="22.222.222-2").exists())

    def test_administrativo_edita(self):
        self.ingresar("administrativo")
        self.client.post(
            reverse("estudiantes:editar_estudiante", args=[self.estudiante.id]),
            {"nombre": "Camila Rojas", "rut": "21.111.111-1",
             "curso": "4° Medio B", "cuenta": "camila.rojas@colegiodigital.cl"},
        )
        self.estudiante.refresh_from_db()
        self.assertEqual(self.estudiante.curso, "4° Medio B")

    def test_administrativo_no_puede_eliminar(self):
        self.ingresar("administrativo")
        self.client.post(
            reverse("estudiantes:eliminar_estudiante", args=[self.estudiante.id])
        )
        self.assertTrue(Estudiante.objects.filter(id=self.estudiante.id).exists())

    def test_administrador_elimina_con_confirmacion(self):
        self.ingresar("admin")
        url = reverse("estudiantes:eliminar_estudiante", args=[self.estudiante.id])
        self.assertContains(self.client.get(url), "¿Estás seguro")
        self.client.post(url)
        self.assertFalse(Estudiante.objects.filter(id=self.estudiante.id).exists())

    def test_docente_y_estudiante_no_acceden_al_crud(self):
        for usuario in ["docente", "estudiante"]:
            with self.subTest(usuario=usuario):
                self.ingresar(usuario)
                self.assertRedirects(
                    self.client.get(reverse("estudiantes:lista_estudiantes")),
                    reverse("inicio_por_perfil"), fetch_redirect_response=False,
                )

    def test_rut_repetido_muestra_error(self):
        self.ingresar("administrativo")
        respuesta = self.client.post(reverse("estudiantes:crear_estudiante"), {
            "nombre": "Otra Persona", "rut": "21.111.111-1",
            "curso": "1° Medio A", "cuenta": "otra@colegiodigital.cl",
        })
        self.assertEqual(Estudiante.objects.filter(rut="21.111.111-1").count(), 1)
        self.assertTrue(respuesta.context["form"].errors)
