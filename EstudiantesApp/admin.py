from django.contrib import admin

from .models import Estudiante, Nota


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "rut", "curso", "cuenta", "usuario"]
    search_fields = ["nombre", "rut", "cuenta", "usuario__username"]
    list_filter = ["curso"]
    autocomplete_fields = ["usuario"]


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "asignatura", "evaluacion", "calificacion", "docente", "fecha_registro")
    list_filter = ("asignatura", "fecha_registro")
    search_fields = ("estudiante__nombre", "estudiante__rut", "evaluacion")
