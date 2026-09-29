from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import Nota

User = get_user_model()


class RegistrarNotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['estudiante', 'asignatura', 'evaluacion', 'calificacion']
        labels = {
            'estudiante': 'Estudiante',
            'asignatura': 'Asignatura',
            'evaluacion': 'Evaluación',
            'calificacion': 'Nota (1,0 a 7,0)',
        }
        widgets = {
            'asignatura': forms.TextInput(attrs={'class': 'form-control'}),
            'evaluacion': forms.TextInput(attrs={'class': 'form-control'}),
            'calificacion': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '1', 'max': '7', 'step': '0.1',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estudiante'].queryset = User.objects.none()
        grupo = Group.objects.filter(name='Estudiante').first()
        if grupo:
            self.fields['estudiante'].queryset = grupo.user_set.order_by('first_name', 'last_name', 'username')
        self.fields['estudiante'].label_from_instance = lambda user: user.get_full_name() or user.username
        self.fields['estudiante'].widget.attrs['class'] = 'form-select'
