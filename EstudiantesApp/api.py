from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.response import Response

from config.api import PermisoPorPerfil, respuestas_error
from .models import Estudiante
from .serializers import EstudianteSerializer


NOTA_CAMPOS_SENSIBLES = (
    '\n\n**Datos sensibles:** `rut`, `cuenta`, `ficha_matricula` y '
    '`usuario` solo aparecen si consulta el **administrador**.'
)


EJEMPLO_ESTUDIANTE = {
    'nombre': 'Juan Pérez',
    'rut': '12345678-9',
    'curso': '4°A',
    'cuenta': 'juan.perez@colegiodigital.cl',
}


@extend_schema_view(
    list=extend_schema(
        summary='Listar estudiantes',
        description=(
            'Lista paginada. Permite buscar con `?search=` '
            '(nombre y curso) y ordenar con `?ordering=nombre`.'
            + NOTA_CAMPOS_SENSIBLES
        ),
        responses={
            200: EstudianteSerializer(many=True),
            **respuestas_error(401, 403),
        },
    ),
    retrieve=extend_schema(
        summary='Ver un estudiante',
        description='Detalle de un estudiante.' + NOTA_CAMPOS_SENSIBLES,
        responses={
            200: EstudianteSerializer,
            **respuestas_error(401, 403, 404),
        },
    ),
    create=extend_schema(
        summary='Registrar un estudiante',
        description=(
            'Perfiles: administrador y administrativo. '
            'Responde 201 con el registro creado.'
        ),
        examples=[
            OpenApiExample(
                'Estudiante',
                value=EJEMPLO_ESTUDIANTE,
                request_only=True,
            )
        ],
        responses={
            201: EstudianteSerializer,
            **respuestas_error(400, 401, 403),
        },
    ),
    update=extend_schema(
        summary='Modificar un estudiante',
        description=(
            'Reemplaza todos los datos del estudiante. '
            'Perfiles: administrador y administrativo.'
        ),
        examples=[
            OpenApiExample(
                'Estudiante',
                value=EJEMPLO_ESTUDIANTE,
                request_only=True,
            )
        ],
        responses={
            200: EstudianteSerializer,
            **respuestas_error(400, 401, 403, 404),
        },
    ),
    destroy=extend_schema(
        summary='Eliminar un estudiante',
        description='Solo el administrador puede eliminar.',
        responses=respuestas_error(401, 403, 404),
    ),
)
@extend_schema(tags=['Estudiantes'])
class EstudianteViewSet(viewsets.ModelViewSet):
    """CRUD de estudiantes con control de acceso por perfil."""

    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    permission_classes = [PermisoPorPerfil]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']

    # Quién puede hacer qué.
    # El administrador siempre puede todo.
    perfiles_lectura = ['administrativo', 'docente']
    perfiles_escritura = ['administrativo']
    perfiles_eliminacion = []

    # Búsqueda y orden solo por campos públicos.
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'curso']
    ordering_fields = ['nombre', 'curso']

    def destroy(self, request, *args, **kwargs):
        estudiante = self.get_object()
        nombre = str(estudiante)
        estudiante.delete()

        return Response(
            {
                'mensaje': f'Estudiante "{nombre}" eliminado correctamente.'
            },
            status=status.HTTP_200_OK,
        )