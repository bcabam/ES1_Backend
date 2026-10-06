from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from config.autorizacion import GRUPOS_POR_PERFIL
from DocentesApp.models import Docente
from EstudiantesApp.models import Estudiante

# Fichas de los mantenedores que pueden tener una cuenta de acceso.
MODELOS_FICHA = {'docente': Docente, 'estudiante': Estudiante}


def opciones_fichas():
    """Fichas de docentes y estudiantes que todavía no tienen cuenta, agrupadas."""
    opciones = [('', 'No enlazar con ninguna ficha')]
    docentes = [
        (f'docente:{docente.pk}', f'{docente.nombre} ({docente.cuenta})')
        for docente in Docente.objects.filter(usuario=None).order_by('nombre')
    ]
    estudiantes = [
        (f'estudiante:{estudiante.pk}', f'{estudiante.nombre} ({estudiante.curso})')
        for estudiante in Estudiante.objects.filter(usuario=None).order_by('nombre')
    ]
    if docentes:
        opciones.append(('Docentes sin cuenta', docentes))
    if estudiantes:
        opciones.append(('Estudiantes sin cuenta', estudiantes))
    return opciones


def buscar_ficha(valor):
    """Convierte "docente:7" en (perfil, ficha). Devuelve (None, None) si no existe."""
    perfil, _, pk = (valor or '').partition(':')
    modelo = MODELOS_FICHA.get(perfil)
    if modelo is None or not pk.isdigit():
        return None, None
    return perfil, modelo.objects.filter(pk=pk, usuario=None).first()


def datos_desde_ficha(valor):
    """Datos iniciales del formulario a partir de una ficha (usuario = parte del correo)."""
    perfil, ficha = buscar_ficha(valor)
    if ficha is None:
        return {}
    nombre, _, apellido = ficha.nombre.partition(' ')
    return {
        'ficha': valor,
        'perfil': perfil,
        'username': ficha.cuenta.split('@')[0].lower(),
        'first_name': nombre,
        'last_name': apellido,
        'email': ficha.cuenta.lower(),
    }


class CrearUsuarioForm(UserCreationForm):
    """Formulario para que el administrador cree usuarios con un perfil."""

    first_name = forms.CharField(label='Nombre', max_length=150)
    last_name = forms.CharField(label='Apellido', max_length=150)
    email = forms.EmailField(label='Correo institucional')
    perfil = forms.ChoiceField(
        label='Perfil',
        choices=[(perfil, nombre) for perfil, nombre in GRUPOS_POR_PERFIL.items()],
    )
    ficha = forms.ChoiceField(
        label='Enlazar con ficha (opcional)',
        required=False,
        help_text='Docente o estudiante del mantenedor que usará esta cuenta.',
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {'username': 'Usuario'}

    field_order = ['ficha', 'perfil', 'username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ficha'].choices = opciones_fichas()
        # Al elegir una ficha se recarga la página para completar sus datos.
        self.fields['ficha'].widget.attrs.update({
            'class': 'form-select',
            'onchange': "if (this.value) { window.location.search = '?ficha=' + this.value; }",
        })
        self.ficha_elegida = None

    def clean_email(self):
        # El correo también sirve para iniciar sesión, por eso no puede repetirse.
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def clean(self):
        datos = super().clean()
        valor = datos.get('ficha')
        if valor:
            perfil_ficha, ficha = buscar_ficha(valor)
            if ficha is None:
                self.add_error('ficha', 'Esa ficha ya no está disponible o ya tiene cuenta.')
            elif datos.get('perfil') != perfil_ficha:
                self.add_error(
                    'perfil',
                    f'Una ficha de {perfil_ficha} solo se puede enlazar con el perfil '
                    f'{GRUPOS_POR_PERFIL[perfil_ficha]}.',
                )
            else:
                self.ficha_elegida = ficha
        return datos

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.is_staff = self.cleaned_data['perfil'] == 'administrador'
        if commit:
            usuario.save()
            nombre_grupo = GRUPOS_POR_PERFIL[self.cleaned_data['perfil']]
            grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
            usuario.groups.set([grupo])
            if self.ficha_elegida:
                self.ficha_elegida.usuario = usuario
                self.ficha_elegida.save(update_fields=['usuario'])
        return usuario
