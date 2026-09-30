from django.contrib import admin

from .models import Docente


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cuenta', 'rut', 'usuario')
    search_fields = ('nombre', 'cuenta', 'rut', 'usuario__username')
    autocomplete_fields = ('usuario',)
    ordering = ('nombre',)
