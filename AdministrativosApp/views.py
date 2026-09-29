from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from config.autorizacion import RUTAS_INICIO, perfil_de, requiere_rol
from .forms import CrearUsuarioForm
from .models import Administrativo


@login_required
def inicio_por_perfil(request):
    """Después del login, envía a cada usuario al inicio de su perfil."""
    perfil = perfil_de(request.user)
    if perfil is None:
        logout(request)
        messages.error(request, 'Tu cuenta no tiene un perfil asignado. Contacta al administrador.')
        return redirect('login')
    return redirect(RUTAS_INICIO[perfil])


@requiere_rol('administrativo')
def inicio_administrativos(request):
    return render(request, 'AdministrativosApp/inicio.html')


@requiere_rol('administrativo')
def listar_funcionarios(request):
    busqueda = request.GET.get('q', '').strip()
    departamento = request.GET.get('departamento', '')

    funcionarios = Administrativo.objects.all()
    if busqueda:
        funcionarios = funcionarios.filter(
            Q(nombre__icontains=busqueda)
            | Q(apellido__icontains=busqueda)
            | Q(cargo__icontains=busqueda)
            | Q(correo_electronico__icontains=busqueda)
        )
    if departamento:
        funcionarios = funcionarios.filter(departamento=departamento)

    departamentos = (
        Administrativo.objects.order_by('departamento')
        .values_list('departamento', flat=True).distinct()
    )

    contexto = {
        'funcionarios': funcionarios,
        'total_funcionarios': funcionarios.count(),
        'departamentos': departamentos,
        'busqueda': busqueda,
        'departamento_seleccionado': departamento,
    }
    return render(request, 'AdministrativosApp/funcionarios.html', contexto)


@requiere_rol('administrador')
def crear_usuario(request):
    """Solo el administrador puede crear usuarios y asignarles un perfil."""
    if request.method == 'POST':
        formulario = CrearUsuarioForm(request.POST)
        if formulario.is_valid():
            usuario = formulario.save()
            messages.success(request, f'Usuario "{usuario.username}" creado correctamente.')
            return redirect('administrativos:crear_usuario')
        messages.error(request, 'Revisa los datos del formulario.')
    else:
        formulario = CrearUsuarioForm()

    return render(request, 'AdministrativosApp/crear_usuario.html', {'formulario': formulario})
