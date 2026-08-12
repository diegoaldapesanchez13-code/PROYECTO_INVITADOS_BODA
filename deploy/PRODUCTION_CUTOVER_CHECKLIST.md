# Checklist de corte a producción — K.8.7.8

## Código
- [ ] `python scripts/verify_stable_k8_7_8.py` = OK.
- [ ] `git status` contiene solo archivos que se desean versionar.
- [ ] commit estable creado.
- [ ] tag estable creado.
- [ ] push GitHub completado.

## Backup origen
- [ ] `db.sqlite3` copiado.
- [ ] hash SHA256 guardado.
- [ ] fixture portable generado.
- [ ] inventario SQLite generado.
- [ ] carpeta `media/` copiada.
- [ ] segunda copia del backup fuera de la PC origen.

## PostgreSQL
- [ ] PostgreSQL instalado en servidor.
- [ ] usuario dedicado `dirtec_app`.
- [ ] contraseña fuerte en `.env.production`.
- [ ] puerto 5432 no expuesto a Internet.
- [ ] migraciones OK.
- [ ] fixture cargado.
- [ ] secuencias reajustadas.
- [ ] inventario PostgreSQL coincide con SQLite.

## Seguridad Django
- [ ] `DJANGO_DEBUG=False`.
- [ ] `DJANGO_SECRET_KEY` real y no versionada.
- [ ] `DJANGO_ALLOWED_HOSTS` sin `*`.
- [ ] `DJANGO_CSRF_TRUSTED_ORIGINS` con HTTPS real.
- [ ] `python manage.py check --deploy` revisado.
- [ ] `SAAS_REQUIRE_SUBSCRIPTION=False` en primer corte deliberadamente.

## Red
- [ ] IP pública real confirmada.
- [ ] CGNAT descartado o alternativa definida.
- [ ] 80/443 apuntan a Caddy.
- [ ] 8001 NO expuesto.
- [ ] 5432 NO expuesto.
- [ ] firewall Windows revisado.

## Caddy
- [ ] dominio correcto.
- [ ] TLS válido.
- [ ] `/static/` funciona.
- [ ] media pública funciona.
- [ ] rutas `/media/documentos/`, `/media/presupuesto/`, `/media/colaboracion/`, `/media/proveedores/`, `/media/tareas/` no son accesibles directamente.
- [ ] `/secure/...` sí funciona para usuarios autorizados.

## Smoke test funcional
- [ ] login DIRTEC.
- [ ] login Empresa.
- [ ] login Planner.
- [ ] login Cliente.
- [ ] login Proveedor.
- [ ] Event Dashboard V3.
- [ ] Portal Cliente.
- [ ] Portal Proveedor.
- [ ] Builder Planner/Empresa.
- [ ] Cliente/Proveedor no pueden abrir Builder por URL.
- [ ] invitados/UUID/RSVP.
- [ ] mesas.
- [ ] agenda/citas.
- [ ] tareas.
- [ ] chat Cliente↔Planner.
- [ ] chat Planner↔Proveedor.
- [ ] documentos privados.
- [ ] Pago Cliente→Empresa.
- [ ] Pago Empresa→Proveedor.
- [ ] invitación pública desde conexión externa.

## Después de publicar
- [ ] revisar `logs/django.log`.
- [ ] backup PostgreSQL programado.
- [ ] backup media programado.
- [ ] servidor configurado para iniciar Waitress/Caddy al arrancar Windows.
- [ ] no realizar desarrollo directo en producción.
