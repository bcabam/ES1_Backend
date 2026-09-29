from django.db import models


class Estudiante(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    curso = models.CharField(max_length=50)
    cuenta = models.EmailField(unique=True)

    def __str__(self):
        return self.nombre