from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


# Definición del modelo Administrativo de colegio
class Administrativo(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administrativo',
        help_text='Cuenta con la que este funcionario inicia sesión.',
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    foto = models.ImageField(upload_to='administrativos/fotos/', blank=True)
    contrato = models.FileField(
        upload_to='administrativos/contratos/',
        blank=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text='Contrato de trabajo en formato PDF.',
    )

    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = 'administrativo'
        verbose_name_plural = 'administrativos'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
