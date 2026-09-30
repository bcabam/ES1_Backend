from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from config.autorizacion import GRUPOS_POR_PERFIL


class CrearUsuarioForm(UserCreationForm):
    """Formulario para que el administrador cree usuarios con un perfil."""

    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo institucional')
    perfil = forms.ChoiceField(
        label='Perfil',
        choices=[(perfil, nombre) for perfil, nombre in GRUPOS_POR_PERFIL.items()],
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {'username': 'Usuario'}

    def clean_email(self):
        # El correo también sirve para iniciar sesión, por eso no puede repetirse.
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = self.cleaned_data['perfil'] == 'administrador'
        if commit:
            usuario.save()
            nombre_grupo = GRUPOS_POR_PERFIL[self.cleaned_data['perfil']]
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
            usuario.groups.set([grupo])
        return usuario
