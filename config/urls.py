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
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from AdministrativosApp import views as administrativos_views

urlpatterns = [
    path('admin/', admin.site.urls),
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
