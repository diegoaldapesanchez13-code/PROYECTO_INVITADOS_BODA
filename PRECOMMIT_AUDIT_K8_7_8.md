# K.8.7.8 — Pre-commit Security & Production Audit

## Resultado

Este baseline corrige los blockers encontrados en la auditoría K.8.7.7 antes de commit/tag y prepara el primer despliegue de producción.

## Corregido antes del commit

1. **Builder por URL directa**
   - Antes: dependía de `eventos_visibles_usuario()`.
   - Ahora: exige `Actions.EVENT_BUILDER` en editor y APIs Builder.
   - Preview borrador también exige `EVENT_BUILDER`.

2. **Portal Cliente**
   - `eventos_para_cliente()` ya no reutiliza la visibilidad general.
   - Requiere relación Cliente real en el evento y membresía CLIENTE activa.

3. **Operación interna**
   - calendario y JSON de calendario → `EVENT_OPERATIONS`;
   - métricas internas → `EVENT_OPERATIONS`;
   - mesas/posiciones → `EVENT_TABLES`;
   - export de invitados → `EVENT_GUESTS`;
   - export financiero/operativo → `EVENT_OPERATIONS`;
   - escrituras del Event Dashboard → `EVENT_EDIT` más controles especializados existentes.

4. **Invitaciones**
   - marcar envío y recordatorio ahora son `POST` + CSRF + `EVENT_GUESTS`.

5. **Legacy Collaboration**
   - rutas HTTP de `ExpedienteServicio` retiradas.
   - tablas/modelos permanecen por compatibilidad de datos; no se borran en este release.

6. **Mensajería destructiva**
   - eliminar mensaje, limpiar historial, eliminar referencia y archivar tema generan `RegistroAuditoria`.
   - archivos físicos se borran con `transaction.on_commit()` para no romper rollback DB/storage.

7. **Media privada**
   - nuevos endpoints `/secure/...` autorizan DocumentoEvento, comprobantes, cotizaciones, adjuntos y evidencias.
   - templates V3 dejan de apuntar directamente a los archivos privados.
   - Caddy bloquea sus carpetas físicas bajo `/media/`.

8. **Login**
   - rate limiting básico por IP + identificador: 10 fallos / 15 min.
   - login fallido/bloqueado queda auditado.

9. **Producción Django**
   - `DEBUG=False` exige SECRET_KEY real, ALLOWED_HOSTS explícitos y PostgreSQL.
   - soporte reverse proxy HTTPS, secure cookies, HSTS configurable, logs rotativos y collectstatic.

10. **Migración SQLite → PostgreSQL**
    - backup exacto SQLite;
    - fixture JSON UTF-8;
    - inventario por modelo y media;
    - hash de archivos media opcional/activado en scripts de corte;
    - reset de secuencias PostgreSQL;
    - comparación automatizada origen/destino.

## Decisiones deliberadas

- Builder no se refactoriza.
- Plantillas/paquetes/capabilities no entran en este release.
- Modelos legacy con datos históricos no se eliminan físicamente.
- `SAAS_REQUIRE_SUBSCRIPTION=False` en el primer corte para no bloquear empresas existentes; se activa en release posterior cuando se valide la lógica comercial final.
- HSTS inicia en 0 durante validación; se aumenta después de confirmar dominio/HTTPS final.

## Blockers restantes antes de hacer commit estable

Solo uno: ejecutar `python scripts/verify_stable_k8_7_8.py` en el venv real de Windows y resolver cualquier regresión que aparezca en el suite global.

## Blockers antes de abrir Internet

- PostgreSQL importado e inventarios iguales.
- `manage.py check --deploy` revisado con `.env.production`.
- IP pública/CGNAT verificados.
- Caddy con HTTPS válido.
- 8001 y 5432 no expuestos.
- smoke tests de todos los roles.
- backup PostgreSQL/media programado.
