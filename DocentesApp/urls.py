from django.urls import path
from . import views

urlpatterns = [
    path('', views.listar_docentes, name='listar_docentes'),
    path('inicio/', views.inicio, name='inicio_docentes'),
    path('crear/', views.crear_docente, name='crear_docente'),
    path('editar/<int:id>/', views.editar_docente, name='editar_docente'),
    path('eliminar/<int:id>/', views.eliminar_docente, name='eliminar_docente'),
    path('listado/', views.listado_docentes, name='listado_docentes'),
    path('notas/', views.notas_docentes, name='notas_docentes'),
]
