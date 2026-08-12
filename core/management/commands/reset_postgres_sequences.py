from django.apps import apps
from django.core.management import BaseCommand
from django.core.management.color import no_style
from django.db import connection


class Command(BaseCommand):
    help = 'Alinea secuencias de PostgreSQL después de cargar fixtures con IDs explícitos.'

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('No es PostgreSQL; no hay secuencias que reajustar con este comando.')
            return
        models = [m for m in apps.get_models() if not m._meta.auto_created]
        statements = connection.ops.sequence_reset_sql(no_style(), models)
        with connection.cursor() as cursor:
            for sql in statements:
                cursor.execute(sql)
        self.stdout.write(self.style.SUCCESS(f'Secuencias reajustadas: {len(statements)} sentencia(s).'))
