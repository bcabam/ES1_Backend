from django.contrib import admin

from .models import Estudiante


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "rut", "curso", "cuenta", "usuario"]
    search_fields = ["nombre", "rut", "cuenta", "usuario__username"]
    list_filter = ["curso"]
    autocomplete_fields = ["usuario"]
