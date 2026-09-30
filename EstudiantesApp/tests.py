from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from DocentesApp.models import Docente

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
        profesora = Docente.objects.create(
            nombre="María Pérez", cuenta="maria.perez@example.com", rut="15.555.555-5"
        )
        nota = Nota.objects.create(
            estudiante=alumno,
            docente=profesora,
            asignatura="Ciencias",
            evaluacion="Evaluación diagnóstica",
            calificacion=Decimal("6.5"),
        )
        self.client.force_login(self.estudiante)
        respuesta = self.client.get(reverse("estudiantes:notas"))

        self.assertContains(respuesta, "Juan Alcachofa")
        self.assertContains(respuesta, nota.asignatura)
        self.assertContains(respuesta, nota.evaluacion)
        self.assertContains(respuesta, "6,5")  # Formato chileno (es-cl).
        self.assertContains(respuesta, "María Pérez")

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


class TransaccionNotasTests(TestCase):
    """Flujo completo: el docente registra y modifica notas; el estudiante las ve."""

    @classmethod
    def setUpTestData(cls):
        call_command("crear_perfiles", "--demo", verbosity=0)
        call_command("loaddata", "estudiantes", verbosity=0)
        cls.juan = Estudiante.objects.get(usuario__username="estudiante")
        cls.camila = Estudiante.objects.get(nombre="Camila Rojas")

    def ingresar(self, usuario):
        self.client.login(username=usuario, password="Colegio2026!")

    def registrar(self, estudiante, calificacion="6.2", asignatura="Química"):
        return self.client.post(reverse("estudiantes:registrar_nota"), {
            "estudiante": estudiante.id, "asignatura": asignatura,
            "evaluacion": "Prueba Unidad 1", "calificacion": calificacion,
        })

    def test_nota_queda_relacionada_con_los_dos_mantenedores(self):
        self.ingresar("docente")
        self.registrar(self.juan)
        nota = Nota.objects.get()
        self.assertIsInstance(nota.docente, Docente)
        self.assertEqual(nota.docente.usuario.username, "docente")
        self.assertEqual(nota.estudiante, self.juan)

    def test_estudiante_ve_nota_registrada_y_modificada(self):
        self.ingresar("docente")
        self.registrar(self.juan, "4.5")
        nota = Nota.objects.get()
        self.client.post(reverse("editar_nota_docente", args=[nota.id]), {
            "estudiante": self.juan.id, "asignatura": "Química",
            "evaluacion": "Prueba Unidad 1", "calificacion": "6.8",
        })

        self.ingresar("estudiante")
        respuesta = self.client.get(reverse("estudiantes:notas"))
        self.assertContains(respuesta, "6,8")
        self.assertNotContains(respuesta, "4,5")

    def test_estudiante_solo_ve_sus_notas_y_puede_buscar(self):
        self.ingresar("docente")
        self.registrar(self.juan, asignatura="Química")
        self.registrar(self.juan, asignatura="Historia")
        self.registrar(self.camila, asignatura="Biología")

        self.ingresar("estudiante")
        respuesta = self.client.get(reverse("estudiantes:notas"))
        self.assertContains(respuesta, "Química")
        self.assertNotContains(respuesta, "Biología")
        respuesta = self.client.get(reverse("estudiantes:notas"), {"q": "hist"})
        self.assertContains(respuesta, "Historia")
        self.assertNotContains(respuesta, "Química")

    def test_docente_busca_notas(self):
        self.ingresar("docente")
        self.registrar(self.juan, asignatura="Química")
        self.registrar(self.camila, asignatura="Biología")
        respuesta = self.client.get(reverse("notas_docentes"), {"q": "camila"})
        self.assertContains(respuesta, "Biología")
        self.assertNotContains(respuesta, "Química")

    def test_docente_sin_ficha_no_puede_registrar(self):
        sin_ficha = User.objects.create_user("profe.nuevo", password="Colegio2026!")
        sin_ficha.groups.add(Group.objects.get(name="Docente"))
        self.ingresar("profe.nuevo")
        respuesta = self.registrar(self.juan)
        self.assertRedirects(
            respuesta, reverse("inicio_por_perfil"), fetch_redirect_response=False
        )
        self.assertFalse(Nota.objects.exists())

    def test_docente_no_edita_notas_de_otro_docente(self):
        otra = Docente.objects.create(
            nombre="Otra Profe", cuenta="otra@example.com", rut="16.666.666-6"
        )
        nota = Nota.objects.create(
            estudiante=self.juan, docente=otra, asignatura="Arte",
            evaluacion="Trabajo", calificacion=Decimal("5.0"),
        )
        self.ingresar("docente")
        respuesta = self.client.get(reverse("editar_nota_docente", args=[nota.id]))
        self.assertEqual(respuesta.status_code, 404)

    def test_ficha_de_matricula_solo_pdf(self):
        self.juan.ficha_matricula = SimpleUploadedFile("ficha.exe", b"MZ")
        with self.assertRaises(ValidationError):
            self.juan.full_clean()

    def test_editar_estudiante_conserva_cuenta_de_acceso(self):
        self.ingresar("administrativo")
        self.client.post(reverse("estudiantes:editar_estudiante", args=[self.juan.id]), {
            "nombre": self.juan.nombre, "rut": self.juan.rut, "curso": "4° Medio B",
            "cuenta": self.juan.cuenta, "usuario": self.juan.usuario_id,
        })
        self.juan.refresh_from_db()
        self.assertEqual(self.juan.curso, "4° Medio B")
        self.assertEqual(self.juan.usuario.username, "estudiante")
