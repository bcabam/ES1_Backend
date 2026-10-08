from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import filters, serializers, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from config.api import PermisoPorPerfil, respuestas_error
from config.autorizacion import perfil_de
from EstudiantesApp.models import Nota
from .models import Docente
from .serializers import DocenteSerializer, NotaSerializer


@extend_schema_view(
    list=extend_schema(
        summary='Listar docentes',
        responses={200: DocenteSerializer(many=True), **respuestas_error(401, 403)},
    ),
    retrieve=extend_schema(
        summary='Ver un docente',
        responses={200: DocenteSerializer, **respuestas_error(401, 403, 404)},
    ),
    create=extend_schema(
        summary='Registrar un docente',
        responses={201: DocenteSerializer, **respuestas_error(400, 401, 403)},
    ),
    update=extend_schema(
        summary='Modificar un docente',
        responses={200: DocenteSerializer, **respuestas_error(400, 401, 403, 404)},
    ),
    destroy=extend_schema(
        summary='Eliminar un docente',
        responses={
            200: inline_serializer(name='DocenteEliminado', fields={'mensaje': serializers.CharField()}),
            **respuestas_error(401, 403, 404),
        },
    ),
)
@extend_schema(tags=['Docentes'])
class DocenteViewSet(viewsets.ModelViewSet):
    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer
    permission_classes = [PermisoPorPerfil]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
    perfiles_lectura = ['administrativo', 'docente']
    perfiles_escritura = ['administrativo']
    perfiles_eliminacion = []
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

    def destroy(self, request, *args, **kwargs):
        docente = self.get_object()
        nombre = str(docente)
        docente.delete()
        return Response(
            {'mensaje': f'Docente "{nombre}" eliminado correctamente.'},
            status=status.HTTP_200_OK,
        )


@extend_schema_view(
    list=extend_schema(
        summary='Listar notas visibles para el perfil autenticado',
        responses={200: NotaSerializer(many=True), **respuestas_error(401, 403)},
    ),
    retrieve=extend_schema(
        summary='Ver una nota',
        responses={200: NotaSerializer, **respuestas_error(401, 403, 404)},
    ),
    create=extend_schema(
        summary='Registrar una nota',
        description='Solo docentes. El docente se asigna desde el usuario autenticado.',
        responses={201: NotaSerializer, **respuestas_error(400, 401, 403)},
    ),
    update=extend_schema(
        summary='Modificar una nota propia',
        responses={200: NotaSerializer, **respuestas_error(400, 401, 403, 404)},
    ),
    destroy=extend_schema(
        summary='Eliminar una nota propia',
        responses={
            200: inline_serializer(name='NotaEliminada', fields={'mensaje': serializers.CharField()}),
            **respuestas_error(401, 403, 404),
        },
    ),
)
@extend_schema(tags=['Notas'])
class NotaViewSet(viewsets.ModelViewSet):
    serializer_class = NotaSerializer
    permission_classes = [PermisoPorPerfil]
    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options']
    perfiles_lectura = ['administrativo', 'docente', 'estudiante']
    perfiles_escritura = ['docente']
    perfiles_eliminacion = ['docente']
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_registro', 'calificacion']

    def get_queryset(self):
        notas = Nota.objects.select_related('estudiante', 'docente')
        perfil = perfil_de(self.request.user)
        if perfil == 'estudiante':
            return notas.filter(estudiante__usuario=self.request.user)
        if perfil == 'docente':
            return notas.filter(docente__usuario=self.request.user)
        return notas

    def perform_create(self, serializer):
        docente = getattr(self.request.user, 'docente', None)
        if docente is None:
            raise PermissionDenied('La cuenta docente no tiene una ficha de Docente asociada.')
        serializer.save(docente=docente)

    def destroy(self, request, *args, **kwargs):
        nota = self.get_object()
        identificador = nota.pk
        nota.delete()
        return Response(
            {'mensaje': f'Nota {identificador} eliminada correctamente.'},
            status=status.HTTP_200_OK,
        )
