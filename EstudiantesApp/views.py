import json
from pathlib import Path

from django.contrib import messages
from django.shortcuts import redirect, render


def cargar_usuarios():
    ruta = Path(__file__).resolve().parent / "data" / "usuarios.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)
from django.shortcuts import render, redirect, get_object_or_404
from .models import Estudiante
from .forms import EstudianteForm
from django.db.models import Q
from django.contrib import messages


def cargar_notas():
    ruta = Path(__file__).resolve().parent / "data" / "notas.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def login(request):
    if request.session.get("usuario_id"):
        return redirect("notas")

    if request.method == "POST":
        correo = request.POST.get("correo", "").strip().lower()
        password = request.POST.get("password", "")

        for usuario in cargar_usuarios():
            if (
                usuario.get("correo", "").lower() == correo
                and usuario.get("password") == password
            ):
                if usuario.get("rol") != "Estudiante":
                    messages.error(
                        request,
                        "Este usuario no pertenece al área de estudiantes.",
                    )
                    return redirect("login")

                request.session.cycle_key()
                request.session["usuario_id"] = usuario["id"]
                request.session["nombre_usuario"] = usuario["nombre"]
                return redirect("notas")

        messages.error(request, "Correo o contraseña incorrectos.")

    return render(request, "estudiantes/login.html")


def notas(request):
    nombre_usuario = request.session.get("nombre_usuario")
    if not nombre_usuario:
        return redirect("login")

    return render(
        request,
        "estudiantes/notas.html",
        {"notas": cargar_notas(), "nombre_usuario": nombre_usuario},
    )


def cerrar_sesion(request):
    if request.method == "POST":
        request.session.flush()
        messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")
def lista_estudiantes(request):
    busqueda = request.GET.get("busqueda", "").strip()

    estudiantes = Estudiante.objects.all()

    if busqueda:
        estudiantes = estudiantes.filter(
            Q(nombre__icontains=busqueda)
            | Q(rut__icontains=busqueda)
            | Q(curso__icontains=busqueda)
        )

    return render(
        request,
        "estudiantes/lista_estudiantes.html",
        {
            "estudiantes": estudiantes,
            "busqueda": busqueda,
        },
    )

def crear_estudiante(request):
    if request.method == "POST":
        form = EstudianteForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Estudiante creado correctamente.")
            return redirect("estudiantes:lista_estudiantes")
    else:
        form = EstudianteForm()

    return render(
        request,
        "estudiantes/crear_estudiantes.html",
        {"form": form},
    )

def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)

    if request.method == "POST":
        form = EstudianteForm(request.POST, instance=estudiante)

        if form.is_valid():
            form.save()
            messages.success(request, "Estudiante actualizado correctamente.")
            return redirect("estudiantes:lista_estudiantes")
    else:
        form = EstudianteForm(instance=estudiante)

    return render(
        request,
        "estudiantes/editar_estudiantes.html",
        {"form": form, "estudiante": estudiante},
    )

def eliminar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)

    if request.method == "POST":
        estudiante.delete()
        messages.success(request, "Estudiante eliminado correctamente.")
        return redirect("estudiantes:lista_estudiantes")

    return render(
        request,
        "estudiantes/eliminar_estudiantes.html",
        {"estudiante": estudiante},
    )
