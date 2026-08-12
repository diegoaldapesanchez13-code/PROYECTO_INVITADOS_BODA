import hashlib
import json
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Genera inventario de registros y archivos para verificar una migración.'

    def add_arguments(self, parser):
        parser.add_argument('output', help='Ruta JSON de salida.')
        parser.add_argument('--hash-media', action='store_true', help='Calcula SHA256 de archivos media (más lento).')

    def handle(self, *args, **options):
        output = Path(options['output']).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        models = {}
        for model in apps.get_models():
            if model._meta.auto_created:
                continue
            label = model._meta.label_lower
            try:
                models[label] = model._default_manager.count()
            except Exception as exc:
                models[label] = {'error': str(exc)}

        media_root = Path(settings.MEDIA_ROOT)
        media = []
        total_bytes = 0
        if media_root.exists():
            for path in sorted(p for p in media_root.rglob('*') if p.is_file()):
                size = path.stat().st_size
                total_bytes += size
                item = {
                    'path': str(path.relative_to(media_root)).replace('\\', '/'),
                    'size': size,
                }
                if options['hash_media']:
                    sha = hashlib.sha256()
                    with path.open('rb') as fh:
                        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
                            sha.update(chunk)
                    item['sha256'] = sha.hexdigest()
                media.append(item)

        payload = {
            'database_vendor': connection.vendor,
            'models': models,
            'media': {
                'count': len(media),
                'total_bytes': total_bytes,
                'files': media,
            },
        }
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Inventario creado: {output}'))
