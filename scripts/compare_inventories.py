import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Uso: python scripts/compare_inventories.py origen.json destino.json')

source = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
target = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

ignore_models = {
    'contenttypes.contenttype',
    'auth.permission',
    'sessions.session',
    'admin.logentry',
}
errors = []
source_models = source.get('models', {})
target_models = target.get('models', {})
for label, count in sorted(source_models.items()):
    if label in ignore_models or isinstance(count, dict):
        continue
    other = target_models.get(label)
    if other != count:
        errors.append(f'{label}: origen={count} destino={other}')

s_media = source.get('media', {})
t_media = target.get('media', {})
if s_media.get('count') != t_media.get('count'):
    errors.append(f"media.count: origen={s_media.get('count')} destino={t_media.get('count')}")
if s_media.get('total_bytes') != t_media.get('total_bytes'):
    errors.append(f"media.total_bytes: origen={s_media.get('total_bytes')} destino={t_media.get('total_bytes')}")

if errors:
    print('MIGRACION: DIFERENCIAS DETECTADAS')
    for item in errors:
        print(' -', item)
    raise SystemExit(1)

print('MIGRACION: INVENTARIOS COINCIDEN')
