from django.db import models

# Definición del modelo Administrativo de colegio
class Administrativo(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    fecha_contratacion = models.DateField()
    puesto = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
