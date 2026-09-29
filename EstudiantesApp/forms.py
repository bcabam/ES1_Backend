from django import forms
from django.contrib.auth.models import Group

from .models import Estudiante, Nota


class EstudianteForm(forms.ModelForm):
    class Meta:
        model = Estudiante
        fields = ["nombre", "rut", "curso", "cuenta", "foto", "usuario"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"
        grupo = Group.objects.filter(name="Estudiante").first()
        self.fields["usuario"].queryset = (
            grupo.user_set.order_by("first_name", "last_name", "username")
            if grupo else self.fields["usuario"].queryset.none()
        )
        self.fields["usuario"].required = False
        self.fields["usuario"].label = "Cuenta de acceso del estudiante"
        self.fields["usuario"].widget.attrs["class"] = "form-select"

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        if len(nombre) < 3:
            raise forms.ValidationError("El nombre debe tener al menos 3 caracteres.")
        return nombre

    def clean_rut(self):
        rut = self.cleaned_data["rut"].strip()
        if len(rut) < 8:
            raise forms.ValidationError("El RUT no tiene un formato válido.")
        return rut

    def clean_curso(self):
        curso = self.cleaned_data["curso"].strip()
        if not curso:
            raise forms.ValidationError("El curso no puede estar vacío.")
        return curso


class RegistrarNotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ["estudiante", "asignatura", "evaluacion", "calificacion"]
        labels = {
            "estudiante": "Estudiante",
            "asignatura": "Asignatura",
            "evaluacion": "Evaluación",
            "calificacion": "Nota (1,0 a 7,0)",
        }
        widgets = {
            "estudiante": forms.Select(attrs={"class": "form-select"}),
            "asignatura": forms.TextInput(attrs={"class": "form-control"}),
            "evaluacion": forms.TextInput(attrs={"class": "form-control"}),
            "calificacion": forms.NumberInput(attrs={
                "class": "form-control", "min": "1", "max": "7", "step": "0.1",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["estudiante"].queryset = Estudiante.objects.order_by("curso", "nombre")
