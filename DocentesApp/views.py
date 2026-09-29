import json
import re
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config.autorizacion import requiere_rol
from .models import Docente


DATA_DIR = Path(__file__).resolve().parent / 'data'


def leer_json(nombre_archivo):
    """Lee los datos de la aplicación sin utilizar base de datos."""
    with (DATA_DIR / nombre_archivo).open(encoding='utf-8') as archivo:
        return json.load(archivo)


def normalizar_rut(rut):
    """Permite ingresar el RUT con o sin puntos, guion o espacios."""
    return re.sub(r'[^0-9Kk]', '', str(rut)).upper()


docente_requerido = requiere_rol('docente')
administrativo_requerido = requiere_rol('administrativo')


def inicio(request):
    """El inicio lo resuelve el login único según el perfil del usuario."""
    return redirect('inicio_por_perfil')


@docente_requerido
def listado_docentes(request):
    estudiantes = leer_json('estudiantes.json')
    cursos = sorted({estudiante['curso'] for estudiante in estudiantes})
    curso_seleccionado = request.GET.get('curso', cursos[0] if cursos else '')
    estudiantes_curso = [
        estudiante for estudiante in estudiantes
        if estudiante['curso'] == curso_seleccionado
    ]
    promedio_general = (
        round(
            sum(estudiante['promedio'] for estudiante in estudiantes_curso)
            / len(estudiantes_curso),
            1,
        )
        if estudiantes_curso else None
    )
    asistencias = [
        asistencia for asistencia in leer_json('asistencia.json')
        if asistencia['curso'] == curso_seleccionado
    ]
    porcentaje_asistencia = (
        round(
            sum(asistencia['porcentaje'] for asistencia in asistencias) / len(asistencias),
            1,
        )
        if asistencias else None
    )

    return render(
        request,
        'DocentesApp/listado.html',
        {
            'estudiantes': estudiantes_curso,
            'cursos': cursos,
            'curso_seleccionado': curso_seleccionado,
            'cantidad_estudiantes': len(estudiantes_curso),
            'promedio_general': promedio_general,
            'asistencias': asistencias,
            'porcentaje_asistencia': porcentaje_asistencia,
            'evaluaciones': [
                evaluacion for evaluacion in leer_json('evaluaciones.json')
                if evaluacion['curso'] == curso_seleccionado
            ],
            'materiales': [
                material for material in leer_json('materiales.json')
                if material['curso'] == curso_seleccionado
            ],
            'mensajes': [
                mensaje for mensaje in leer_json('mensajes.json')
                if mensaje['curso'] == curso_seleccionado
            ],
            'docente': {'nombre': request.user.get_full_name() or request.user.username},
        },
    )


@administrativo_requerido
def listar_docentes(request):
    busqueda = request.GET.get('q', '').strip()
    docentes = Docente.objects.all()
    if busqueda:
        filtros = (
            Q(nombre__icontains=busqueda)
            | Q(cuenta__icontains=busqueda)
            | Q(rut__icontains=busqueda)
        )
        rut_buscado = normalizar_rut(busqueda)
        if any(caracter.isdigit() for caracter in busqueda) and rut_buscado:
            ids_rut = [
                docente_id
                for docente_id, rut in Docente.objects.values_list('id', 'rut')
                if rut_buscado in normalizar_rut(rut)
            ]
            filtros |= Q(id__in=ids_rut)
        docentes = docentes.filter(filtros)
    return render(
        request,
        'docentes/listar.html',
        {'docentes': docentes, 'busqueda': busqueda},
    )


def _validar_datos_docente(nombre, cuenta, rut, docente_actual=None):
    if not nombre or not cuenta or not rut:
        return 'Completa todos los campos.'
    if len(nombre) > 150 or len(cuenta) > 254 or len(rut) > 12:
        return 'Uno de los campos supera la longitud permitida.'
    try:
        validate_email(cuenta)
    except ValidationError:
        return 'Ingresa una cuenta de correo válida.'

    docentes = Docente.objects.all()
    if docente_actual:
        docentes = docentes.exclude(pk=docente_actual.pk)
    if docentes.filter(cuenta__iexact=cuenta).exists():
        return 'Ya existe un docente con esa cuenta.'
    rut_normalizado = normalizar_rut(rut)
    if any(normalizar_rut(item) == rut_normalizado for item in docentes.values_list('rut', flat=True)):
        return 'Ya existe un docente con ese RUT.'
    return None


@administrativo_requerido
def crear_docente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cuenta = request.POST.get('cuenta', '').strip()
        rut = request.POST.get('rut', '').strip()

        error = _validar_datos_docente(nombre, cuenta, rut)
        if error:
            return render(
                request,
                'docentes/crear.html',
                {
                    'error': error,
                    'nombre': nombre,
                    'cuenta': cuenta,
                    'rut': rut,
                },
            )
        Docente.objects.create(nombre=nombre, cuenta=cuenta, rut=rut)
        messages.success(request, 'Docente creado correctamente.')
        return redirect('listar_docentes')

    return render(request, 'docentes/crear.html')


@administrativo_requerido
def editar_docente(request, id):
    docente = get_object_or_404(Docente, id=id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cuenta = request.POST.get('cuenta', '').strip()
        rut = request.POST.get('rut', '').strip()

        error = _validar_datos_docente(nombre, cuenta, rut, docente)
        if error:
            docente.nombre = nombre
            docente.cuenta = cuenta
            docente.rut = rut
            return render(
                request,
                'docentes/editar.html',
                {'docente': docente, 'error': error},
            )
        docente.nombre = nombre
        docente.cuenta = cuenta
        docente.rut = rut
        docente.save()
        messages.success(request, 'Datos del docente actualizados correctamente.')
        return redirect('listar_docentes')

    return render(request, 'docentes/editar.html', {'docente': docente})


@require_POST
@requiere_rol('administrador')  # El operador (administrativo) no puede eliminar.
def eliminar_docente(request, id):
    docente = get_object_or_404(Docente, id=id)
    docente.delete()
    messages.success(request, 'Docente eliminado correctamente.')
    return redirect('listar_docentes')
