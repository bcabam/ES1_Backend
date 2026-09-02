from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


RUTAS_INICIO = {
    "administrativo": "administrativos:inicio",
    "docente": "listado_docentes",
    "estudiante": "estudiantes:notas",
}

RUTAS_LOGIN = {
    "administrativo": "administrativos:login",
    "docente": "login",
    "estudiante": "estudiantes:login",
}


def rol_activo(request):
    """Obtiene el único rol autorizado para la sesión actual."""
    rol = request.session.get("rol")
    if rol in RUTAS_INICIO:
        return rol
    return None


def redirigir_si_hay_sesion(request):
    """Impide iniciar sesión en otra área sin cerrar la sesión activa."""
    rol = rol_activo(request)
    if rol:
        messages.info(request, "Cierra tu sesión actual antes de ingresar a otra área.")
        return redirect(RUTAS_INICIO[rol])
    return None


def requiere_rol(rol_requerido):
    """Protege una vista y evita que un rol acceda al panel de otro."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            rol = rol_activo(request)
            if rol == rol_requerido:
                return vista(request, *args, **kwargs)
            if rol:
                messages.error(request, "No tienes permisos para acceder a esa área.")
                return redirect(RUTAS_INICIO[rol])
            return redirect(RUTAS_LOGIN[rol_requerido])

        return envoltura

    return decorador
