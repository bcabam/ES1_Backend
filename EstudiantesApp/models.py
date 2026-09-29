from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Nota(models.Model):
    estudiante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notas_registradas',
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='notas_ingresadas',
    )
    asignatura = models.CharField(max_length=100)
    evaluacion = models.CharField(max_length=150)
    calificacion = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_registro']

    def __str__(self):
        return f'{self.estudiante} - {self.asignatura}: {self.calificacion}'
