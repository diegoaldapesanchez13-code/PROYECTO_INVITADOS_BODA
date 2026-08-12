from django.db import migrations


def migrar_mensajes_legacy(apps, schema_editor):
    ExpedienteServicio = apps.get_model("colaboracion", "ExpedienteServicio")
    MensajeExpediente = apps.get_model("colaboracion", "MensajeExpediente")
    ConversacionServicio = apps.get_model("colaboracion", "ConversacionServicio")
    MensajeServicio = apps.get_model("colaboracion", "MensajeServicio")
    AdjuntoMensajeServicio = apps.get_model("colaboracion", "AdjuntoMensajeServicio")

    expedientes = ExpedienteServicio.objects.exclude(servicio_evento_id=None)
    for expediente in expedientes.iterator():
        for legacy in MensajeExpediente.objects.filter(expediente_id=expediente.id).order_by("fecha", "id"):
            conversacion, _ = ConversacionServicio.objects.get_or_create(
                servicio_evento_id=expediente.servicio_evento_id,
                canal=legacy.canal,
                defaults={"creada_por_id": legacy.autor_id},
            )
            # Evita duplicar si una base fue preparada manualmente antes de aplicar la migracion.
            existente = MensajeServicio.objects.filter(
                conversacion_id=conversacion.id,
                autor_id=legacy.autor_id,
                tipo=legacy.tipo,
                texto=legacy.mensaje or "",
                fecha=legacy.fecha,
            ).first()
            if existente:
                nuevo = existente
            else:
                nuevo = MensajeServicio.objects.create(
                    conversacion_id=conversacion.id,
                    autor_id=legacy.autor_id,
                    tipo=legacy.tipo,
                    texto=legacy.mensaje or "",
                )
                MensajeServicio.objects.filter(id=nuevo.id).update(fecha=legacy.fecha)

            if legacy.archivo and not AdjuntoMensajeServicio.objects.filter(
                mensaje_id=nuevo.id,
                archivo=legacy.archivo.name,
            ).exists():
                nombre = legacy.archivo.name.rsplit("/", 1)[-1]
                AdjuntoMensajeServicio.objects.create(
                    mensaje_id=nuevo.id,
                    archivo=legacy.archivo.name,
                    nombre_original=nombre[:255],
                )


def reverse_noop(apps, schema_editor):
    # No borramos informacion migrada en rollback para evitar perdida de historial.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("colaboracion", "0002_service_workspace_k84"),
    ]

    operations = [
        migrations.RunPython(migrar_mensajes_legacy, reverse_noop),
    ]
