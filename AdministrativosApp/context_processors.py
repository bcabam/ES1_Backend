def usuario_actual(request):
    return {
        'usuario_actual': request.session.get('usuario_actual'),
        'nombre_actual': request.session.get('nombre_actual'),
    }
