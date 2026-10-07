from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.autorizacion import perfil_de


@extend_schema(
    tags=['Autenticación'],
    summary='Obtener tokens JWT',
    description=(
        'Recibe usuario (o correo) y contraseña. Devuelve un **access token** (15 minutos), '
        'que se usa en "Authorize", y un **refresh token** (1 día) para renovarlo.'
    ),
    examples=[
        OpenApiExample(
            'Docente de prueba',
            value={'username': 'docente', 'password': 'Colegio2026!'},
            request_only=True,
        ),
    ],
)
class ObtenerTokenView(TokenObtainPairView):
    # Máximo 10 intentos por minuto desde una misma IP (protección contra fuerza bruta).
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'token'


@extend_schema(
    tags=['Autenticación'],
    summary='Renovar el access token',
    description=(
        'Recibe el refresh token y devuelve un access token nuevo y un refresh nuevo. '
        'El refresh usado queda invalidado (no se puede reutilizar).'
    ),
)
class RenovarTokenView(TokenRefreshView):
    pass


class MiPerfilView(APIView):
    """Devuelve los datos de la cuenta dueña del token."""

    @extend_schema(
        tags=['Autenticación'],
        summary='Mi perfil',
        description='Endpoint protegido: sin un access token válido responde 401.',
        responses=inline_serializer(
            name='MiPerfil',
            fields={
                'usuario': serializers.CharField(),
                'nombre': serializers.CharField(),
                'perfil': serializers.CharField(allow_null=True),
            },
        ),
    )
    def get(self, request):
        usuario = request.user
        return Response({
            'usuario': usuario.get_username(),
            'nombre': usuario.get_full_name(),
            'perfil': perfil_de(usuario),
        })
