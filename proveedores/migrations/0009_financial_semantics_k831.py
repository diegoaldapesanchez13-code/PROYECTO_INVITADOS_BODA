# Generated for DIRTEC Event Studio K.8.3.1
from decimal import Decimal

from django.db import migrations, models


ZERO = Decimal('0')


def backfill_financial_semantics(apps, schema_editor):
    ServicioEvento = apps.get_model('proveedores', 'ServicioEvento')

    for servicio in ServicioEvento.objects.all().iterator():
        precio_cliente = servicio.precio_cliente or ZERO
        costo_total = servicio.costo_total or ZERO
        ajuste_cliente = servicio.ajuste_cliente or ZERO

        # El mejor dato historico disponible para el valor comercial es el
        # precio_cliente introducido en K.8.2; si no existe, conservamos el
        # antiguo costo_total como fallback sin descartar informacion.
        valor = precio_cliente if precio_cliente != ZERO else costo_total

        if servicio.modalidad == 'INCLUIDO':
            cargo = ZERO
        elif servicio.modalidad == 'UPGRADE':
            # Solo migramos una diferencia que ya estuviera explicitamente
            # registrada como ajuste; no inferimos un upgrade desde precio.
            cargo = ajuste_cliente
        elif servicio.modalidad == 'ADICIONAL' and servicio.origen in {'CATALOGO', 'PAQUETE'}:
            cargo = precio_cliente
        else:
            # Los registros legacy fueron marcados MANUAL/ADICIONAL durante
            # K.8.2 aunque el campo antiguo mezclaba costo y precio. Para no
            # inventar deuda del cliente, el cargo nuevo parte en cero.
            cargo = ZERO

        ServicioEvento.objects.filter(pk=servicio.pk).update(
            valor_contratado=valor,
            cargo_adicional_cliente=max(cargo, ZERO),
        )


class Migration(migrations.Migration):
    dependencies = [
        ('proveedores', '0008_package_materialization_k83'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicioevento',
            name='valor_contratado',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='servicioevento',
            name='cargo_adicional_cliente',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(backfill_financial_semantics, migrations.RunPython.noop),
    ]
