"""Rutas de la API de AdministrativosApp (se publican bajo /api/)."""

from rest_framework.routers import SimpleRouter

from .api import AdministrativoViewSet

router = SimpleRouter()
# /api/administrativos/        GET (listar), POST (crear)
# /api/administrativos/<id>/   GET (ver), PUT (modificar), DELETE (eliminar)
router.register('administrativos', AdministrativoViewSet, basename='api-administrativos')

urlpatterns = router.urls
