import json
from pathlib import Path

from django.shortcuts import render

from config.autorizacion import requiere_rol


def cargar_notas():
    ruta = Path(__file__).resolve().parent / "data" / "notas.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


@requiere_rol("estudiante")
def notas(request):
    nombre_usuario = request.user.get_full_name() or request.user.username

    return render(
        request,
        "estudiantes/notas.html",
        {"notas": cargar_notas(), "nombre_usuario": nombre_usuario},
    )
