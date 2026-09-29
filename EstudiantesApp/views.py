from django.contrib import messages
from django.shortcuts import redirect, render

from config.autorizacion import requiere_rol
from .forms import RegistrarNotaForm
from .models import Nota


@requiere_rol("estudiante")
def notas(request):
    nombre_usuario = request.user.get_full_name() or request.user.username

    return render(
        request,
        "estudiantes/notas.html",
        {
            "notas": Nota.objects.filter(estudiante=request.user).select_related('docente'),
            "nombre_usuario": nombre_usuario,
        },
    )


@requiere_rol('docente')
def registrar_nota(request):
    if request.method == 'POST':
        formulario = RegistrarNotaForm(request.POST)
        if formulario.is_valid():
            nota = formulario.save(commit=False)
            nota.docente = request.user
            nota.save()
            messages.success(request, 'La nota se registró correctamente.')
            return redirect('estudiantes:registrar_nota')
    else:
        formulario = RegistrarNotaForm()

    return render(request, 'estudiantes/registrar_nota.html', {'formulario': formulario})
