from django.urls import path
from . import views

app_name = "estudiantes"

urlpatterns = [
    path("notas/", views.notas, name="notas"),
]
