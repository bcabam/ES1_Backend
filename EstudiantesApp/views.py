import json
from pathlib import Path

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from config.autorizacion import requiere_rol
from .forms import EstudianteForm
from .models import Estudiante


def cargar_notas():
    ruta = Path(__file__).resolve().parent / "data" / "notas.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


@requiere_rol("estudiante")
def notas(request):
    nombre_usuario = request.user.get_full_name() or request.user.username

    return render(
        request,
        "estudiantes/notas.html",
        {"notas": cargar_notas(), "nombre_usuario": nombre_usuario},
    )


@requiere_rol("administrativo")
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


@requiere_rol("administrativo")
def crear_estudiante(request):
    if request.method == "POST":
        form = EstudianteForm(request.POST, request.FILES)

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


@requiere_rol("administrativo")
def editar_estudiante(request, estudiante_id):
    estudiante = get_object_or_404(Estudiante, id=estudiante_id)

    if request.method == "POST":
        form = EstudianteForm(request.POST, request.FILES, instance=estudiante)

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


@requiere_rol("administrador")  # El operador (administrativo) no puede eliminar.
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
