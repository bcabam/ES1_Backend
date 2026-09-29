from django.conf import settings
from django.db import models


class Estudiante(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    curso = models.CharField(max_length=50)
    cuenta = models.EmailField(unique=True)
    foto = models.ImageField(upload_to="estudiantes/fotos/", blank=True)
    # Cuenta con la que el estudiante inicia sesión para ver sus notas (opcional).
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estudiante",
    )

    class Meta:
        ordering = ["curso", "nombre"]

    def __str__(self):
        return self.nombre
