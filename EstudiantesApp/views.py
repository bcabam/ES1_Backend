from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from config.autorizacion import requiere_rol
from .forms import EstudianteForm, RegistrarNotaForm
from .models import Estudiante, Nota


@requiere_rol("estudiante")
def notas(request):
    nombre_usuario = request.user.get_full_name() or request.user.username
    try:
        estudiante = request.user.estudiante
        notas_estudiante = Nota.objects.filter(estudiante=estudiante).select_related("docente")
    except Estudiante.DoesNotExist:
        notas_estudiante = Nota.objects.none()

    return render(
        request,
        "estudiantes/notas.html",
        {"notas": notas_estudiante, "nombre_usuario": nombre_usuario},
    )


@requiere_rol("docente")
def registrar_nota(request):
    if request.method == "POST":
        formulario = RegistrarNotaForm(request.POST)
        if formulario.is_valid():
            nota = formulario.save(commit=False)
            nota.docente = request.user
            nota.save()
            messages.success(request, "La nota se registró correctamente.")
            return redirect("estudiantes:registrar_nota")
    else:
        formulario = RegistrarNotaForm()

    return render(request, "estudiantes/registrar_nota.html", {"formulario": formulario})


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
        {"estudiantes": estudiantes, "busqueda": busqueda},
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
    return render(request, "estudiantes/crear_estudiantes.html", {"form": form})


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


@requiere_rol("administrador")
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
