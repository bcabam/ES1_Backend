from django.contrib import admin

from .models import Nota


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('estudiante', 'asignatura', 'evaluacion', 'calificacion', 'docente', 'fecha_registro')
    list_filter = ('asignatura', 'fecha_registro')
    search_fields = ('estudiante__username', 'estudiante__first_name', 'estudiante__last_name', 'evaluacion')

# Register your models here.
