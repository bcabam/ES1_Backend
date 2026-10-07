"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from AdministrativosApp import api as administrativos_api
from AdministrativosApp import views as administrativos_views

# Rutas de la API REST (JSON, protegidas con JWT).
api_urlpatterns = [
    path('token/', administrativos_api.ObtenerTokenView.as_view(), name='token'),
    path('token/refresh/', administrativos_api.RenovarTokenView.as_view(), name='token_refresh'),
    path('perfil/', administrativos_api.MiPerfilView.as_view(), name='mi_perfil'),
    # Documentación: esquema OpenAPI y Swagger UI.
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
    # Login único para todos los perfiles (Django Authentication).
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='AdministrativosApp/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('panel/', administrativos_views.inicio_por_perfil, name='inicio_por_perfil'),
    path(
        'administrativos/',
        include(('AdministrativosApp.urls', 'administrativos'), namespace='administrativos'),
    ),
    path('', include('DocentesApp.urls')),
    path(
        'estudiantes/',
        include(('EstudiantesApp.urls', 'estudiantes'), namespace='estudiantes'),
    ),
]

# Errores 404 y 500 en JSON cuando la ruta es de la API.
handler404 = 'config.api.pagina_no_encontrada'
handler500 = 'config.api.error_del_servidor'

# En desarrollo, Django sirve las fotos y documentos subidos.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
