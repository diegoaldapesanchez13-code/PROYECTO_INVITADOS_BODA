from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("proveedores", "0005_proveedor_contacto_operativo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="servicioevento",
            name="estado_proveedor",
            field=models.CharField(
                choices=[
                    ("PENDIENTE", "Pendiente de confirmar"),
                    ("CONFIRMADO", "Confirmado por proveedor"),
                    ("INCIDENCIA", "Requiere atencion"),
                    ("COMPLETADO", "Servicio realizado"),
                ],
                default="PENDIENTE",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="servicioevento",
            name="comentario_proveedor",
            field=models.TextField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="servicioevento",
            name="fecha_respuesta_proveedor",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
    ]
