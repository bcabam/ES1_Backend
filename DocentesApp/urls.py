from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
    path('', views.inicio, name='inicio_docentes'),
    path('listado/', views.listado_docentes, name='listado_docentes'),
]
