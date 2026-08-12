import json
from pathlib import Path

from django.core.management import BaseCommand, call_command
from django.db import connection


EXCLUDES = [
    'contenttypes',
    'auth.permission',
    'auth.group',
    'sessions',
    'admin.logentry',
]


class Command(BaseCommand):
    help = 'Exporta los datos portables del proyecto a JSON UTF-8 para migrar SQLite -> PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument('output', help='Ruta del archivo JSON de salida.')

    def handle(self, *args, **options):
        output = Path(options['output']).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        self.stdout.write(f'Base actual: {connection.vendor}')
        self.stdout.write(f'Exportando a: {output}')
        with output.open('w', encoding='utf-8', newline='') as fh:
            call_command(
                'dumpdata',
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                exclude=EXCLUDES,
                stdout=fh,
            )
        self.stdout.write(self.style.SUCCESS('Exportación portable completada.'))
