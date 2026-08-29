from django.urls import path

from . import views

app_name = 'administrativos'

urlpatterns = [
    path('', views.inicio_administrativos, name='inicio'),
    path('funcionarios/', views.listar_funcionarios, name='listar_funcionarios'),
    path('registro/', views.registro_usuario, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
]
