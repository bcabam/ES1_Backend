from django.urls import path

from . import views

app_name = "estudiantes"

urlpatterns = [
    path("notas/", views.notas, name="notas"),
    path("notas/registrar/", views.registrar_nota, name="registrar_nota"),
    path("estudiantes/", views.lista_estudiantes, name="lista_estudiantes"),
    path("estudiantes/nuevo/", views.crear_estudiante, name="crear_estudiante"),
    path(
        "estudiantes/editar/<int:estudiante_id>/",
        views.editar_estudiante,
        name="editar_estudiante",
    ),
    path(
        "estudiantes/eliminar/<int:estudiante_id>/",
        views.eliminar_estudiante,
        name="eliminar_estudiante",
    ),
]
