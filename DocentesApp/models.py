from django.conf import settings
from django.db import models


class Docente(models.Model):
    nombre = models.CharField(max_length=150)
    cuenta = models.EmailField(unique=True)
    rut = models.CharField(max_length=12, unique=True)
    # Cuenta con la que el docente inicia sesión para registrar notas (opcional).
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='docente',
    )

    def __str__(self):
        return self.nombre
