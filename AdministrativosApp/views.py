import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from config.autorizacion import RUTAS_INICIO, perfil_de, requiere_rol
from .forms import CrearUsuarioForm

RUTA_DATOS_FUNCIONARIOS = Path(settings.BASE_DIR) / 'datos' / 'funcionarios.json'


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
    with open(RUTA_DATOS_FUNCIONARIOS, 'r', encoding='utf-8') as archivo:
        datos_funcionarios = json.load(archivo)

    departamentos = sorted({funcionario['departamento'] for funcionario in datos_funcionarios})

    contexto = {
        'funcionarios': datos_funcionarios,
        'total_funcionarios': len(datos_funcionarios),
        'departamentos': departamentos,
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
