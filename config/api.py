"""Piezas de seguridad compartidas por todos los endpoints de la API."""

import logging

from django.http import JsonResponse
from django.views import defaults
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.views import exception_handler

from config.autorizacion import perfil_de

logger = logging.getLogger(__name__)


class PermisoPorPerfil(BasePermission):
    """Autoriza según el perfil del usuario y la acción solicitada.

    Cada vista declara qué perfiles pueden hacer cada cosa:

        perfiles_lectura = ['administrativo', 'docente']   # GET
        perfiles_escritura = ['administrativo']            # POST, PUT, PATCH
        perfiles_eliminacion = []                          # DELETE

    El administrador siempre tiene acceso completo.
    """

    ACCIONES = {'lectura': 'consultar', 'escritura': 'crear o modificar', 'eliminacion': 'eliminar'}

    def has_permission(self, request, view):
        perfil = perfil_de(request.user)
        if perfil is None:
            self.message = 'Tu cuenta no tiene un perfil asignado.'
            return False
        if perfil == 'administrador':
            return True

        if request.method in SAFE_METHODS:
            tipo = 'lectura'
        elif request.method == 'DELETE':
            tipo = 'eliminacion'
        else:
            tipo = 'escritura'

        if perfil in getattr(view, f'perfiles_{tipo}', ()):
            return True
        self.message = f'El perfil {perfil} no tiene permiso para {self.ACCIONES[tipo]} este recurso.'
        return False


class OcultaCamposSensiblesMixin:
    """Quita de las respuestas los campos sensibles si quien consulta no es administrador.

    Uso en un serializer:

        class DocenteSerializer(OcultaCamposSensiblesMixin, serializers.ModelSerializer):
            class Meta:
                model = Docente
                fields = ['id', 'nombre', 'rut', 'cuenta']
                campos_sensibles = ['rut', 'cuenta']

    Los campos sensibles se pueden enviar al crear o modificar, pero solo el
    administrador los recibe de vuelta.
    """

    def to_representation(self, instancia):
        datos = super().to_representation(instancia)
        request = self.context.get('request')
        if request is None or perfil_de(request.user) != 'administrador':
            for campo in getattr(self.Meta, 'campos_sensibles', ()):
                datos.pop(campo, None)
        return datos


MENSAJES_POR_CODIGO = {
    status.HTTP_400_BAD_REQUEST: 'Los datos enviados no son válidos.',
    status.HTTP_401_UNAUTHORIZED: 'Debes autenticarte con un token válido.',
    status.HTTP_403_FORBIDDEN: 'No tienes permiso para realizar esta acción.',
    status.HTTP_404_NOT_FOUND: 'El recurso solicitado no existe.',
    status.HTTP_405_METHOD_NOT_ALLOWED: 'Método no permitido en este endpoint.',
    status.HTTP_429_TOO_MANY_REQUESTS: 'Demasiadas solicitudes. Intenta nuevamente en un momento.',
}


def manejador_errores(exc, context):
    """Entrega todos los errores de la API con el mismo formato JSON.

    {"error": "mensaje descriptivo", "codigo": 400, "detalle": {...}}

    Los errores inesperados responden 500 sin revelar información interna.
    """
    respuesta = exception_handler(exc, context)

    if respuesta is None:
        logger.exception('Error no controlado en la API', exc_info=exc)
        return Response(
            {'error': 'Ocurrió un error interno del servidor. Intenta nuevamente más tarde.',
             'codigo': status.HTTP_500_INTERNAL_SERVER_ERROR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    datos = respuesta.data
    cuerpo = {'codigo': respuesta.status_code}
    if isinstance(datos, dict) and 'detail' in datos:
        datos = dict(datos)
        cuerpo['error'] = str(datos.pop('detail'))
        datos.pop('code', None)
        if datos:
            cuerpo['detalle'] = datos
    else:
        cuerpo['error'] = MENSAJES_POR_CODIGO.get(respuesta.status_code, 'No se pudo procesar la solicitud.')
        cuerpo['detalle'] = datos
    respuesta.data = cuerpo
    return respuesta


def _es_api(request):
    return request.path.startswith('/api/')


def pagina_no_encontrada(request, exception):
    """404 en JSON para rutas de la API; página normal para el sitio web."""
    if _es_api(request):
        return JsonResponse(
            {'error': MENSAJES_POR_CODIGO[404], 'codigo': 404}, status=404
        )
    return defaults.page_not_found(request, exception)


def error_del_servidor(request):
    """500 en JSON para rutas de la API, sin detalles internos."""
    if _es_api(request):
        return JsonResponse(
            {'error': 'Ocurrió un error interno del servidor. Intenta nuevamente más tarde.',
             'codigo': 500},
            status=500,
        )
    return defaults.server_error(request)
