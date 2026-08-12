# K.8.3 — Package Snapshot & Service Materialization

## Objetivo

Extender K.8.2 sin crear otro proyecto, otra app de runtime ni otro entorno virtual.
La fase conserva `PaqueteBoda` como catalogo maestro, congela el acuerdo en
`PaqueteEvento` y materializa servicios operativos independientes en
`proveedores.ServicioEvento`.

## Flujo

`PaqueteBoda` maestro -> `PaqueteEvento.snapshot_paquete` -> `ServicioEvento`
independientes con `origen=PAQUETE` y `modalidad=INCLUIDO`.

## Cambios

### `paquetes.PaqueteEvento`

- `snapshot_paquete`: JSON contractual congelado.
- `snapshot_generado_en`: fecha de captura.
- `materializado_en`: ultima materializacion.
- `materializacion_version`: version de la estrategia.
- Validacion multiempresa paquete/evento.

### `proveedores.ServicioEvento`

- `paquete_evento`: asignacion contractual que origino el servicio.
- `servicio_paquete_origen`: item maestro que lo origino.
- `paquete_nombre_snapshot`.
- `paquete_servicio_snapshot`.
- `cantidad_paquete`.
- Constraint idempotente por paquete + item maestro.

### Servicio de dominio `paquetes/services.py`

- `construir_snapshot_paquete()`
- `capturar_snapshot_paquete()`
- `materializar_servicios_paquete()`

La materializacion es explicita e idempotente: volver a ejecutarla actualiza
las instancias ya creadas sin duplicarlas.

## Compatibilidad

- No se elimina ningun campo legacy.
- No se modifica Builder.
- No se crea nueva venv.
- No se toca `settings.py` ni URLs.
- Los `PaqueteEvento` existentes migran con snapshot vacio y sin materializar.
- Servicios manuales/catalogo existentes permanecen intactos.

## Admin

`PaqueteEventoAdmin` incorpora dos acciones:

1. **K.8.3 - Capturar snapshot contractual**.
2. **K.8.3 - Materializar servicios del paquete**.

El snapshot y las fechas quedan en solo lectura.

## Instalacion sobre K.8.2

Copiar/reemplazar solo los archivos incluidos en el paquete K.8.3 y ejecutar,
desde la misma raiz Django y con la misma venv:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py test paquetes.tests paquetes.tests_k83 proveedores.tests_event_domain_k82
```

No ejecutar `makemigrations` salvo que el `--check --dry-run` reporte una
diferencia inesperada; las migraciones K.8.3 ya estan incluidas.
