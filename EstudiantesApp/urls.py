from django.urls import path
from . import views

app_name = "estudiantes"

urlpatterns = [
    path("notas/", views.notas, name="notas"),
    path("notas/registrar/", views.registrar_nota, name="registrar_nota"),
]
