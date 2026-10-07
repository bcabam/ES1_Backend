from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import filters, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.api import PermisoPorPerfil, respuestas_error
from config.autorizacion import perfil_de
from .models import Administrativo
from .serializers import AdministrativoSerializer


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


NOTA_CAMPOS_SENSIBLES = (
    '\n\n**Datos sensibles:** `correo_electronico`, `telefono`, `fecha_contratacion`, '
    '`contrato` y `usuario` solo aparecen si consulta el **administrador**.'
)

EJEMPLO_FUNCIONARIO = {
    'nombre': 'Marcela', 'apellido': 'Rojas', 'cargo': 'Directora',
    'departamento': 'Dirección Académica', 'correo_electronico': 'marcela.rojas@colegiodigital.cl',
    'telefono': '+56 9 1234 5678',
}


@extend_schema_view(
    list=extend_schema(
        summary='Listar funcionarios',
        description=(
            'Lista paginada. Permite buscar con `?search=` (nombre, apellido, cargo, '
            'departamento) y ordenar con `?ordering=apellido`.' + NOTA_CAMPOS_SENSIBLES
        ),
        responses={200: AdministrativoSerializer(many=True), **respuestas_error(401, 403)},
    ),
    retrieve=extend_schema(
        summary='Ver un funcionario',
        description='Detalle de un funcionario.' + NOTA_CAMPOS_SENSIBLES,
        responses={200: AdministrativoSerializer, **respuestas_error(401, 403, 404)},
    ),
    create=extend_schema(
        summary='Registrar un funcionario',
        description='Perfiles: administrador y administrativo. Responde 201 con el registro creado.',
        examples=[OpenApiExample('Funcionario', value=EJEMPLO_FUNCIONARIO, request_only=True)],
        responses={201: AdministrativoSerializer, **respuestas_error(400, 401, 403)},
    ),
    update=extend_schema(
        summary='Modificar un funcionario',
        description='Reemplaza todos los datos del funcionario. Perfiles: administrador y administrativo.',
        examples=[OpenApiExample('Funcionario', value=EJEMPLO_FUNCIONARIO, request_only=True)],
        responses={200: AdministrativoSerializer, **respuestas_error(400, 401, 403, 404)},
    ),
    destroy=extend_schema(
        summary='Eliminar un funcionario',
        description='Solo el administrador puede eliminar.',
        responses={
            200: inline_serializer(name='Eliminado', fields={'mensaje': serializers.CharField()}),
            **respuestas_error(401, 403, 404),
        },
    ),
)
@extend_schema(tags=['Funcionarios (Administrativos)'])
class AdministrativoViewSet(viewsets.ModelViewSet):
    """CRUD de funcionarios administrativos con control de acceso por perfil."""

    queryset = Administrativo.objects.all()
    serializer_class = AdministrativoSerializer
    permission_classes = [PermisoPorPerfil]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    # Quién puede hacer qué (el administrador siempre puede todo).
    perfiles_lectura = ['administrativo', 'docente', 'estudiante']
    perfiles_escritura = ['administrativo']
    perfiles_eliminacion = []

    # Búsqueda y orden solo por campos públicos (no se puede buscar por datos sensibles).
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'apellido', 'cargo', 'departamento']
    ordering_fields = ['nombre', 'apellido', 'cargo', 'departamento']

    def destroy(self, request, *args, **kwargs):
        funcionario = self.get_object()
        nombre = str(funcionario)
        funcionario.delete()
        return Response(
            {'mensaje': f'Funcionario "{nombre}" eliminado correctamente.'},
            status=status.HTTP_200_OK,
        )
