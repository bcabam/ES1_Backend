import django.db.models.deletion
from django.db import migrations, models


def enlazar_notas_con_docentes(apps, schema_editor):
    """Pasa cada nota del usuario que la registró a su ficha de Docente.

    Busca la ficha enlazada a ese usuario o, si no hay enlace, la que tenga su
    mismo correo. Las notas de prueba que no calzan con ninguna ficha se eliminan,
    porque una nota siempre debe pertenecer a un docente del mantenedor.
    """
    Nota = apps.get_model("EstudiantesApp", "Nota")
    Docente = apps.get_model("DocentesApp", "Docente")
    for nota in Nota.objects.select_related("docente"):
        usuario = nota.docente
        ficha = Docente.objects.filter(usuario=usuario).first()
        if ficha is None and usuario.email:
            ficha = Docente.objects.filter(cuenta__iexact=usuario.email).first()
        if ficha:
            nota.docente_ficha = ficha
            nota.save(update_fields=["docente_ficha"])
        else:
            nota.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("DocentesApp", "0002_docente_usuario"),
        ("EstudiantesApp", "0003_nota"),
    ]

    operations = [
        migrations.AddField(
            model_name="nota",
            name="docente_ficha",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="DocentesApp.docente",
            ),
        ),
        migrations.RunPython(enlazar_notas_con_docentes, migrations.RunPython.noop),
        migrations.RemoveField(model_name="nota", name="docente"),
        migrations.RenameField(model_name="nota", old_name="docente_ficha", new_name="docente"),
        migrations.AlterField(
            model_name="nota",
            name="docente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="notas_ingresadas",
                to="DocentesApp.docente",
            ),
        ),
    ]
