from rest_framework import serializers

from config.api import OcultaCamposSensiblesMixin
from EstudiantesApp.models import Nota
from .models import Docente


class DocenteSerializer(OcultaCamposSensiblesMixin, serializers.ModelSerializer):
    usuario = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = Docente
        fields = ['id', 'nombre', 'rut', 'cuenta', 'usuario']
        campos_sensibles = ['rut', 'cuenta', 'usuario']

    def validate_nombre(self, valor):
        valor = valor.strip()
        if len(valor) < 3:
            raise serializers.ValidationError('El nombre debe tener al menos 3 caracteres.')
        return valor

    def validate_rut(self, valor):
        return valor.strip()

    def validate_cuenta(self, valor):
        return valor.strip().lower()


class NotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nota
        fields = [
            'id', 'estudiante', 'docente', 'asignatura', 'evaluacion',
            'calificacion', 'fecha_registro',
        ]
        read_only_fields = ['docente', 'fecha_registro']

    def validate_asignatura(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError('La asignatura es obligatoria.')
        return valor

    def validate_evaluacion(self, valor):
        valor = valor.strip()
        if not valor:
            raise serializers.ValidationError('La evaluación es obligatoria.')
        return valor
