# DIRTEC Event Studio

Plataforma Django multiempresa para operación de eventos, planners, clientes, proveedores, invitados, RSVP, servicios, agenda, tareas, documentos, pagos e invitaciones digitales.

## Baseline

La línea K.8 cierra la primera plataforma Event-Centric estable. El objetivo de K.8.7.8 es ser el baseline que se despliega por primera vez en producción.

## Roles

```text
DIRTEC
  └── Empresa
       ├── Administrador / Ventas
       ├── Wedding Planner
       ├── Cliente
       └── Proveedor
```

El aislamiento por empresa y evento se valida en backend; ocultar botones en templates no se considera autorización.

## Dominio operativo

`EventoBoda` es el contexto principal del evento y `ServicioEvento` es la fuente de verdad de servicios contratados/operativos.

Cada servicio puede tener:
- canal Cliente ↔ Planner;
- canal Planner ↔ Proveedor;
- notas internas;
- cotizaciones versionadas;
- propuestas/aprobaciones;
- tareas;
- citas/actividades;
- documentos;
- egresos/pagos al proveedor.

## Finanzas

Los dos flujos se mantienen separados:

```text
Cliente → PagoClienteEvento → Empresa/Planner
Empresa → GastoEvento/PagoEvento → Proveedor
```

## Invitados

- `Grupoinvitacion`: enlace/UUID de invitación.
- `Invitado`: persona individual y fuente de verdad de RSVP.
- Mesas/asignaciones trabajan sobre invitados individuales.

## Invitaciones visuales

Hay dos conceptos independientes:

1. **DIRTEC Builder**: editor visual existente, congelado funcionalmente en este baseline.
2. **Plantillas genéricas**: módulo futuro separado, todavía no implementado como producto final.

Builder no se modifica para implementar plantillas. En el futuro su acceso se habilitará mediante capacidades/paquetes sin cambiar su motor interno.

## Desarrollo local

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
py manage.py migrate
py manage.py runserver
```

SQLite continúa soportado para desarrollo/offline.

## Producción

El baseline de producción utiliza:

```text
Windows Server PC
├── Caddy HTTPS / reverse proxy
├── Waitress WSGI (127.0.0.1:8001)
├── Django
└── PostgreSQL (127.0.0.1:5432)
```

El dominio/DNS puede administrarse desde Hostinger y apuntar a la IP pública del servidor.

Ver:
- `deploy/DEPLOYMENT_WINDOWS_POSTGRES_HOSTINGER.md`
- `deploy/PRODUCTION_CUTOVER_CHECKLIST.md`

## Datos existentes

Nunca borrar `db.sqlite3` para migrar a PostgreSQL. El proceso oficial genera:
- copia exacta SQLite;
- fixture JSON UTF-8;
- inventario de registros;
- inventario/hash de media;
- comparación origen/destino.

## Gate estable

Antes de commit/tag de producción:

```powershell
python scripts/verify_stable_k8_7_8.py
```

El gate focalizado y el suite completo deben terminar en OK.
