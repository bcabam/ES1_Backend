from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class UsuarioOCorreoBackend(ModelBackend):
    """Permite iniciar sesión con el nombre de usuario o con el correo.

    Si lo ingresado contiene "@", se busca la cuenta por su correo (sin
    distinguir mayúsculas). Si hay más de una cuenta con ese correo, no se
    inicia sesión, para no entrar a una cuenta equivocada.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username and '@' in username:
            cuentas = get_user_model().objects.filter(email__iexact=username.strip())
            if cuentas.count() != 1:
                return None
            username = cuentas.get().get_username()
        return super().authenticate(request, username=username, password=password, **kwargs)
