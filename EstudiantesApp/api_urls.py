"""Rutas de la API de EstudiantesApp (se publican bajo /api/).

Para agregar un endpoint, sigue la guía API.md: registra tu ViewSet en el router.
Ejemplo:
    from .api import EstudianteViewSet
    router.register('estudiantes', EstudianteViewSet, basename='api-estudiantes')
"""

from rest_framework.routers import SimpleRouter

router = SimpleRouter()

urlpatterns = router.urls
