from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from config.autorizacion import GRUPOS_POR_PERFIL


# Permisos de cada perfil, con el formato "app.accion_modelo".
# Si un modelo todavía no existe, su permiso se omite con un aviso:
# basta con volver a ejecutar el comando cuando el modelo esté creado.
PERMISOS_POR_GRUPO = {
    # Administrador: crear, modificar, eliminar y consultar todo.
    'Administrador': [
        'DocentesApp.add_docente', 'DocentesApp.change_docente',
        'DocentesApp.delete_docente', 'DocentesApp.view_docente',
        'EstudiantesApp.add_estudiante', 'EstudiantesApp.change_estudiante',
        'EstudiantesApp.delete_estudiante', 'EstudiantesApp.view_estudiante',
        'DocentesApp.add_registronota', 'DocentesApp.change_registronota',
        'DocentesApp.delete_registronota', 'DocentesApp.view_registronota',
    ],
    # Administrativo (perfil Operador): crea, modifica y consulta; no elimina.
    'Administrativo': [
        'DocentesApp.add_docente', 'DocentesApp.change_docente', 'DocentesApp.view_docente',
        'EstudiantesApp.add_estudiante', 'EstudiantesApp.change_estudiante',
        'EstudiantesApp.view_estudiante',
        'DocentesApp.view_registronota',
    ],
    # Docente: registra y modifica notas de sus estudiantes.
    'Docente': [
        'EstudiantesApp.view_estudiante',
        'DocentesApp.add_registronota', 'DocentesApp.change_registronota',
        'DocentesApp.view_registronota',
    ],
    # Estudiante (perfil Consulta): solo visualiza.
    'Estudiante': [
        'DocentesApp.view_registronota',
    ],
}

USUARIOS_DEMO = [
    ('admin', 'Ana', 'Administradora', 'Administrador'),
    ('administrativo', 'Pedro', 'Secretaría', 'Administrativo'),
    ('docente', 'María', 'Pérez', 'Docente'),
    ('estudiante', 'Juan', 'González', 'Estudiante'),
]
CLAVE_DEMO = 'Colegio2026!'


class Command(BaseCommand):
    help = 'Crea los grupos de perfiles con sus permisos (y usuarios de prueba con --demo).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo', action='store_true',
            help='Crea además un usuario de prueba por perfil (solo para desarrollo).',
        )

    def handle(self, *args, **opciones):
        if opciones['verbosity'] == 0:
            self.stdout.write = lambda *a, **k: None
        for nombre_grupo in GRUPOS_POR_PERFIL.values():
            grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
            permisos = []
            for permiso in PERMISOS_POR_GRUPO[nombre_grupo]:
                app, codigo = permiso.split('.')
                encontrado = Permission.objects.filter(
                    content_type__app_label=app, codename=codigo
                ).first()
                if encontrado:
                    permisos.append(encontrado)
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  Aviso: el permiso {permiso} aún no existe (falta el modelo).'
                    ))
            grupo.permissions.set(permisos)
            estado = 'creado' if creado else 'actualizado'
            self.stdout.write(self.style.SUCCESS(
                f'Grupo {nombre_grupo} {estado} con {len(permisos)} permisos.'
            ))

        if opciones['demo']:
            self.crear_usuarios_demo()

    def crear_usuarios_demo(self):
        for usuario_nombre, nombre, apellido, nombre_grupo in USUARIOS_DEMO:
            usuario, creado = User.objects.get_or_create(
                username=usuario_nombre,
                defaults={
                    'first_name': nombre,
                    'last_name': apellido,
                    'email': f'{usuario_nombre}@colegiodigital.cl',
                },
            )
            if creado:
                usuario.set_password(CLAVE_DEMO)
            usuario.is_staff = nombre_grupo == 'Administrador'
            usuario.is_superuser = nombre_grupo == 'Administrador'
            usuario.save()
            usuario.groups.set([Group.objects.get(name=nombre_grupo)])
            self.stdout.write(f'Usuario de prueba: {usuario_nombre} / {CLAVE_DEMO} ({nombre_grupo})')
