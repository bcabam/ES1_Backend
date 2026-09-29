from django.contrib import admin
from django.utils.html import format_html

from .models import Administrativo


@admin.register(Administrativo)
class AdministrativoAdmin(admin.ModelAdmin):
    list_display = ['miniatura', 'nombre', 'apellido', 'cargo', 'departamento',
                    'correo_electronico', 'usuario', 'tiene_contrato']
    list_display_links = ['nombre', 'apellido']
    search_fields = ['nombre', 'apellido', 'cargo', 'correo_electronico', 'usuario__username']
    list_filter = ['departamento', 'cargo']
    autocomplete_fields = ['usuario']

    @admin.display(description='Foto')
    def miniatura(self, administrativo):
        if administrativo.foto:
            return format_html('<img src="{}" style="height:40px;border-radius:50%;">',
                               administrativo.foto.url)
        return '—'

    @admin.display(description='Contrato', boolean=True)
    def tiene_contrato(self, administrativo):
        return bool(administrativo.contrato)
