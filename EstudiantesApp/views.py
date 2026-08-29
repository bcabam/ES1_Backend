import json
from pathlib import Path

from django.contrib import messages
from django.shortcuts import redirect, render

from config.autorizacion import redirigir_si_hay_sesion, requiere_rol


def cargar_usuarios():
    ruta = Path(__file__).resolve().parent / "data" / "usuarios.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def cargar_notas():
    ruta = Path(__file__).resolve().parent / "data" / "notas.json"
    with ruta.open(encoding="utf-8") as archivo:
        return json.load(archivo)


def login(request):
    redireccion = redirigir_si_hay_sesion(request)
    if redireccion:
        return redireccion

    if request.method == "POST":
        correo = request.POST.get("correo", "").strip().lower()
        password = request.POST.get("password", "")

        for usuario in cargar_usuarios():
            if (
                usuario.get("correo", "").lower() == correo
                and usuario.get("password") == password
            ):
                if usuario.get("rol") != "Estudiante":
                    messages.error(
                        request,
                        "Este usuario no pertenece al área de estudiantes.",
                    )
                    return redirect("estudiantes:login")

                request.session.flush()
                request.session["rol"] = "estudiante"
                request.session["usuario_id"] = usuario["id"]
                request.session["nombre_usuario"] = usuario["nombre"]
                return redirect("estudiantes:notas")

        messages.error(request, "Correo o contraseña incorrectos.")

    return render(request, "estudiantes/login.html")


@requiere_rol("estudiante")
def notas(request):
    nombre_usuario = request.session["nombre_usuario"]

    return render(
        request,
        "estudiantes/notas.html",
        {"notas": cargar_notas(), "nombre_usuario": nombre_usuario},
    )


def cerrar_sesion(request):
    if request.method == "POST":
        request.session.flush()
        messages.success(request, "Sesión cerrada correctamente.")
    return redirect("estudiantes:login")
