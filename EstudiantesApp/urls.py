from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login, name="login"),
    path("notas/", views.notas, name="notas"),
    path("logout/", views.cerrar_sesion, name="logout"),
]
