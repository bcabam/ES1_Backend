from config.autorizacion import perfil_de


def perfil_usuario(request):
    """Deja disponible {{ perfil }} en todas las plantillas para armar el menú."""
    return {'perfil': perfil_de(request.user)}
