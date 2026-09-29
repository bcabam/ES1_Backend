from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect


# Cada perfil corresponde a un Grupo de Django (tabla auth_group).
GRUPOS_POR_PERFIL = {
    "administrador": "Administrador",
    "administrativo": "Administrativo",
    "docente": "Docente",
    "estudiante": "Estudiante",
}

RUTAS_INICIO = {
    "administrador": "administrativos:inicio",
    "administrativo": "administrativos:inicio",
    "docente": "listado_docentes",
    "estudiante": "estudiantes:notas",
}


def perfil_de(usuario):
    """Devuelve el perfil del usuario según el grupo al que pertenece."""
    if not usuario.is_authenticated:
        return None
    if usuario.is_superuser:
        return "administrador"

    grupos_usuario = set(usuario.groups.values_list("name", flat=True))
    for perfil, nombre_grupo in GRUPOS_POR_PERFIL.items():
        if nombre_grupo in grupos_usuario:
            return perfil
    return None


def requiere_rol(*roles_permitidos):
    """Protege una vista: exige sesión iniciada y uno de los perfiles indicados.

    El administrador tiene acceso a todas las áreas.
    """
    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())

            perfil = perfil_de(request.user)
            if perfil == "administrador" or perfil in roles_permitidos:
                return vista(request, *args, **kwargs)

            messages.error(request, "No tienes permisos para acceder a esa área.")
            return redirect("inicio_por_perfil")

        return envoltura

    return decorador
