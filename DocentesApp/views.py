import json
import re
from functools import wraps
from pathlib import Path

from django.shortcuts import redirect, render


DATA_DIR = Path(__file__).resolve().parent / 'data'


def leer_json(nombre_archivo):
    """Lee los datos de la aplicación sin utilizar base de datos."""
    with (DATA_DIR / nombre_archivo).open(encoding='utf-8') as archivo:
        return json.load(archivo)


def normalizar_rut(rut):
    """Permite ingresar el RUT con o sin puntos, guion o espacios."""
    return re.sub(r'[^0-9Kk]', '', str(rut)).upper()


def docente_requerido(vista):
    """Restringe las vistas del docente a una sesión iniciada."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if 'docente' not in request.session:
            return redirect('login')
        return vista(request, *args, **kwargs)
    return envoltura


def iniciar_sesion(request):
    """Valida la cuenta y el RUT definidos en docentes.json."""
    if 'docente' in request.session:
        return redirect('listado_docentes')

    error = None
    if request.method == 'POST':
        cuenta = request.POST.get('cuenta', '').strip()
        rut = normalizar_rut(request.POST.get('rut', ''))
        docente = next(
            (
                item for item in leer_json('docentes.json')
                if str(item.get('cuenta', '')).strip().casefold() == cuenta.casefold()
                and normalizar_rut(item['rut']) == rut
            ),
            None,
        )
        if docente:
            request.session['docente'] = {
                'nombre': docente['nombre'],
                'cuenta': docente['cuenta'],
            }
            return redirect('listado_docentes')
        error = 'La cuenta o el RUT no son válidos.'

    return render(
        request,
        'DocentesApp/login.html',
        {'error': error, 'cuenta': request.POST.get('cuenta', '')},
    )


def cerrar_sesion(request):
    request.session.flush()
    return redirect('login')


def inicio(request):
    return redirect('login')


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
            'docente': request.session['docente'],
        },
    )
