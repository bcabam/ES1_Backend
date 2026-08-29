import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect, render

RUTA_DATOS_FUNCIONARIOS = Path(settings.BASE_DIR) / 'datos' / 'funcionarios.json'
RUTA_DATOS_USUARIOS = Path(settings.BASE_DIR) / 'datos' / 'usuarios.json'


def inicio_administrativos(request):
    return render(request, 'AdministrativosApp/inicio.html')


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


def _cargar_usuarios():
    with open(RUTA_DATOS_USUARIOS, 'r', encoding='utf-8') as archivo:
        return json.load(archivo)


def _guardar_usuarios(datos_usuarios):
    with open(RUTA_DATOS_USUARIOS, 'w', encoding='utf-8') as archivo:
        json.dump(datos_usuarios, archivo, ensure_ascii=False, indent=4)


def registro_usuario(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        contrasena = request.POST.get('contrasena', '')
        confirmar_contrasena = request.POST.get('confirmar_contrasena', '')

        datos_usuarios = _cargar_usuarios()

        if not usuario or not nombre or not contrasena:
            messages.error(request, 'Todos los campos son obligatorios.')
        elif contrasena != confirmar_contrasena:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif any(u['usuario'] == usuario for u in datos_usuarios):
            messages.error(request, 'Ese nombre de usuario ya existe.')
        else:
            datos_usuarios.append({
                'usuario': usuario,
                'nombre': nombre,
                'contrasena_hash': make_password(contrasena),
            })
            _guardar_usuarios(datos_usuarios)
            messages.success(request, 'Cuenta creada correctamente. Ahora puedes iniciar sesión.')
            return redirect('administrativos:login')

    return render(request, 'AdministrativosApp/registro.html')


def iniciar_sesion(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        contrasena = request.POST.get('contrasena', '')

        datos_usuarios = _cargar_usuarios()
        usuario_encontrado = next((u for u in datos_usuarios if u['usuario'] == usuario), None)

        if usuario_encontrado and check_password(contrasena, usuario_encontrado['contrasena_hash']):
            request.session['usuario_actual'] = usuario_encontrado['usuario']
            request.session['nombre_actual'] = usuario_encontrado['nombre']
            messages.success(request, f"Bienvenido, {usuario_encontrado['nombre']}.")
            return redirect('administrativos:inicio')

        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'AdministrativosApp/login.html')


def cerrar_sesion(request):
    request.session.flush()
    messages.info(request, 'Sesión cerrada.')
    return redirect('administrativos:inicio')
