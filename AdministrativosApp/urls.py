from django.urls import path

from . import views

app_name = 'administrativos'

urlpatterns = [
    path('', views.inicio_administrativos, name='inicio'),
    path('funcionarios/', views.listar_funcionarios, name='listar_funcionarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
]
