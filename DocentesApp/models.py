from django.db import models


class Docente(models.Model):
    nombre = models.CharField(max_length=150)
    cuenta = models.EmailField(unique=True)
    rut = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.nombre
