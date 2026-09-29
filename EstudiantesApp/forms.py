from django import forms
from .models import Estudiante


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ["nombre", "rut", "curso", "cuenta"]

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()

        if len(nombre) < 3:
            raise forms.ValidationError(
                "El nombre debe tener al menos 3 caracteres."
            )

        return nombre

    def clean_rut(self):
        rut = self.cleaned_data["rut"].strip()

        if len(rut) < 8:
            raise forms.ValidationError(
                "El RUT no tiene un formato válido."
            )

        return rut

    def clean_curso(self):
        curso = self.cleaned_data["curso"].strip()

        if not curso:
            raise forms.ValidationError(
                "El curso no puede estar vacío."
            )

        return curso