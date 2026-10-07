import re

from rest_framework import serializers

from config.api import OcultaCamposSensiblesMixin, validar_tamano_archivo
from .models import Administrativo


class AdministrativoSerializer(OcultaCamposSensiblesMixin, serializers.ModelSerializer):
    """Funcionario administrativo del colegio.

    Correo, teléfono, contrato y cuenta de acceso son datos sensibles:
    solo el administrador los recibe en las respuestas.
    """

    usuario = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Administrativo
        fields = [
            'id', 'nombre', 'apellido', 'cargo', 'departamento', 'foto',
            'correo_electronico', 'telefono', 'fecha_contratacion', 'contrato', 'usuario',
        ]
        campos_sensibles = [
            'correo_electronico', 'telefono', 'fecha_contratacion', 'contrato', 'usuario',
        ]

    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError('El nombre debe tener al menos 2 caracteres.')
        return valor

    def validate_apellido(self, valor):
        return self.validate_nombre(valor)

    def validate_correo_electronico(self, valor):
        return valor.strip().lower()

    def validate_telefono(self, valor):
        if valor and not re.fullmatch(r'\+?[\d\s]{8,20}', valor):
            raise serializers.ValidationError(
                'Teléfono no válido: usa solo números, espacios y un "+" inicial (8 a 20 caracteres).'
            )
        return valor

    def validate_foto(self, archivo):
        return validar_tamano_archivo(archivo, maximo_mb=2)

    def validate_contrato(self, archivo):
        return validar_tamano_archivo(archivo, maximo_mb=5)
