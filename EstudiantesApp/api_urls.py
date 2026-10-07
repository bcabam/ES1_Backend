"""Rutas de la API de Estudiantes (se publican bajo /api/)."""

from rest_framework.routers import SimpleRouter

from .api import EstudianteViewSet


router = SimpleRouter()

# /api/estudiantes/        GET (listar), POST (crear)
# /api/estudiantes/<id>/   GET (ver), PUT (modificar), DELETE (eliminar)
router.register(
    'estudiantes',
    EstudianteViewSet,
    basename='api-estudiantes',
)

urlpatterns = router.urls