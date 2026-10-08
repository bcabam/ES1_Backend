"""Rutas de la API de DocentesApp (se publican bajo /api/).

Para agregar un endpoint, sigue la guía API.md: registra tu ViewSet en el router.
Ejemplo:
    from .api import DocenteViewSet
    router.register('docentes', DocenteViewSet, basename='api-docentes')
"""

from rest_framework.routers import SimpleRouter

from .api import DocenteViewSet, NotaViewSet

router = SimpleRouter()
router.register('docentes', DocenteViewSet, basename='api-docentes')
router.register('notas', NotaViewSet, basename='api-notas')

urlpatterns = router.urls
