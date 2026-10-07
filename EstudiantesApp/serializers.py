from rest_framework import serializers

from config.api import OcultaCamposSensiblesMixin, validar_tamano_archivo
from .models import Estudiante


class EstudianteSerializer(OcultaCamposSensiblesMixin, serializers.ModelSerializer):
    """Estudiante del colegio.

    RUT, cuenta, ficha de matrícula y usuario son datos sensibles:
    solo el administrador los recibe en las respuestas.
    """

    usuario = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
    )

    class Meta:
        model = Estudiante
        fields = [
            'id',
            'nombre',
            'rut',
            'curso',
            'cuenta',
            'foto',
            'ficha_matricula',
            'usuario',
        ]
        campos_sensibles = [
            'rut',
            'cuenta',
            'ficha_matricula',
            'usuario',
        ]

    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 3:
            raise serializers.ValidationError(
                'El nombre debe tener al menos 3 caracteres.'
            )
        return valor

    def validate_curso(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError(
                'El curso no puede estar vacío.'
            )
        return valor

    def validate_foto(self, archivo):
        return validar_tamano_archivo(archivo, maximo_mb=2)

    def validate_ficha_matricula(self, archivo):
        return validar_tamano_archivo(archivo, maximo_mb=5)