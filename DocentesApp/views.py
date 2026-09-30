import re

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from config.autorizacion import requiere_rol
from EstudiantesApp.models import Estudiante, Nota
from EstudiantesApp.forms import RegistrarNotaForm
from .models import Docente


def ficha_docente(usuario):
    """Ficha del mantenedor Docente enlazada a la cuenta que inició sesión."""
    return getattr(usuario, 'docente', None)


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
    cursos = list(Estudiante.objects.order_by("curso").values_list("curso", flat=True).distinct())
    curso_seleccionado = request.GET.get("curso", cursos[0] if cursos else "")
    estudiantes_curso = Estudiante.objects.filter(curso=curso_seleccionado).annotate(
        promedio=Avg("notas__calificacion")
    )
    promedio_general = Nota.objects.filter(
        estudiante__curso=curso_seleccionado
    ).aggregate(promedio=Avg("calificacion"))["promedio"]
    notas_curso = Nota.objects.filter(
        estudiante__curso=curso_seleccionado
    ).select_related("estudiante")
    return render(request, "DocentesApp/listado.html", {
        "estudiantes": estudiantes_curso,
        "notas_curso": notas_curso,
        "cursos": cursos,
        "curso_seleccionado": curso_seleccionado,
        "cantidad_estudiantes": estudiantes_curso.count(),
        "promedio_general": promedio_general,
        "asistencias": [],
        "porcentaje_asistencia": None,
        "evaluaciones": [],
        "materiales": [],
        "mensajes": [],
        "docente": {"nombre": getattr(ficha_docente(request.user), 'nombre', None)
                    or request.user.get_full_name() or request.user.username},
    })


@docente_requerido
def notas_docentes(request):
    curso = request.GET.get("curso", "").strip()
    busqueda = request.GET.get("q", "").strip()
    notas = Nota.objects.select_related("estudiante", "docente")
    if curso:
        notas = notas.filter(estudiante__curso=curso)
    if busqueda:
        notas = notas.filter(
            Q(estudiante__nombre__icontains=busqueda)
            | Q(estudiante__rut__icontains=busqueda)
            | Q(asignatura__icontains=busqueda)
            | Q(evaluacion__icontains=busqueda)
        )
    cursos = Estudiante.objects.order_by("curso").values_list("curso", flat=True).distinct()
    return render(request, "DocentesApp/notas.html", {
        "notas": notas,
        "cursos": cursos,
        "curso_seleccionado": curso,
        "busqueda": busqueda,
        "mi_ficha": ficha_docente(request.user),
    })


@docente_requerido
def editar_nota_docente(request, nota_id):
    # Cada docente solo puede modificar las notas que él mismo registró.
    nota = get_object_or_404(Nota, pk=nota_id, docente__usuario=request.user)
    if request.method == "POST":
        formulario = RegistrarNotaForm(request.POST, instance=nota)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, "La nota se actualizó correctamente.")
            return redirect("notas_docentes")
    else:
        formulario = RegistrarNotaForm(instance=nota)
    return render(request, "DocentesApp/editar_nota.html", {
        "formulario": formulario,
        "nota": nota,
    })


@docente_requerido
def eliminar_nota_docente(request, nota_id):
    # Cada docente solo puede eliminar las notas que él mismo registró.
    nota = get_object_or_404(Nota, pk=nota_id, docente__usuario=request.user)
    if request.method == "POST":
        nota.delete()
        messages.success(request, "La nota se eliminó correctamente.")
        return redirect("notas_docentes")
    return render(request, "DocentesApp/eliminar_nota.html", {"nota": nota})


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


def _cuentas_disponibles(docente_actual=None):
    """Cuentas del grupo Docente que aún no están enlazadas a otra ficha."""
    cuentas = User.objects.filter(groups__name='Docente').order_by('first_name', 'username')
    ocupadas = Docente.objects.exclude(usuario=None)
    if docente_actual:
        ocupadas = ocupadas.exclude(pk=docente_actual.pk)
    return cuentas.exclude(pk__in=ocupadas.values('usuario'))


def _cuenta_elegida(request, docente_actual=None):
    """Devuelve (cuenta, error) según la opción elegida en el formulario."""
    usuario_id = request.POST.get('usuario', '')
    if not usuario_id:
        return None, None
    cuenta = _cuentas_disponibles(docente_actual).filter(pk=usuario_id).first()
    if cuenta is None:
        return None, 'La cuenta elegida no es válida o ya está enlazada a otro docente.'
    return cuenta, None


@administrativo_requerido
def crear_docente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cuenta = request.POST.get('cuenta', '').strip()
        rut = request.POST.get('rut', '').strip()

        cuenta_acceso, error_cuenta = _cuenta_elegida(request)
        error = _validar_datos_docente(nombre, cuenta, rut) or error_cuenta
        if error:
            return render(
                request,
                'docentes/crear.html',
                {
                    'error': error,
                    'nombre': nombre,
                    'cuenta': cuenta,
                    'rut': rut,
                    'cuentas': _cuentas_disponibles(),
                    'usuario_id': request.POST.get('usuario', ''),
                },
            )
        Docente.objects.create(nombre=nombre, cuenta=cuenta, rut=rut, usuario=cuenta_acceso)
        messages.success(request, 'Docente creado correctamente.')
        return redirect('listar_docentes')

    return render(request, 'docentes/crear.html', {'cuentas': _cuentas_disponibles()})


@administrativo_requerido
def editar_docente(request, id):
    docente = get_object_or_404(Docente, id=id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        cuenta = request.POST.get('cuenta', '').strip()
        rut = request.POST.get('rut', '').strip()

        cuenta_acceso, error_cuenta = _cuenta_elegida(request, docente)
        error = _validar_datos_docente(nombre, cuenta, rut, docente) or error_cuenta
        if error:
            docente.nombre = nombre
            docente.cuenta = cuenta
            docente.rut = rut
            return render(
                request,
                'docentes/editar.html',
                {'docente': docente, 'error': error, 'cuentas': _cuentas_disponibles(docente)},
            )
        docente.nombre = nombre
        docente.cuenta = cuenta
        docente.rut = rut
        docente.usuario = cuenta_acceso
        docente.save()
        messages.success(request, 'Datos del docente actualizados correctamente.')
        return redirect('listar_docentes')

    return render(
        request,
        'docentes/editar.html',
        {'docente': docente, 'cuentas': _cuentas_disponibles(docente)},
    )


@require_POST
@requiere_rol('administrador')  # El operador (administrativo) no puede eliminar.
def eliminar_docente(request, id):
    docente = get_object_or_404(Docente, id=id)
    docente.delete()
    messages.success(request, 'Docente eliminado correctamente.')
    return redirect('listar_docentes')
