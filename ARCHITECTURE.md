# DIRTEC Event Studio — arquitectura baseline K.8.7.8

## 1. Principios

- multiempresa con aislamiento en backend;
- autorización por acción, no por visibilidad de UI;
- Event-Centric;
- `ServicioEvento` como fuente de verdad de servicios;
- Cliente y Proveedor son identidades externas con portales limitados;
- Planner/Empresa operan el evento;
- DIRTEC conserva administración global;
- Builder y plantillas son productos visuales independientes;
- datos y media deben poder respaldarse/restaurarse.

## 2. Jerarquía

```text
DIRTEC
  ↓
EmpresaSuscriptora
  ↓
EventoBoda
  ├── Planner
  ├── Clientes
  ├── Invitados / grupos / RSVP / mesas
  ├── ServicioEvento
  │    ├── Cliente ↔ Planner
  │    ├── Planner ↔ Proveedor
  │    ├── Interno
  │    ├── cotizaciones / propuestas / aprobaciones
  │    ├── tareas / agenda
  │    ├── documentos
  │    └── gastos/pagos proveedor
  └── PagoClienteEvento
```

## 3. Autorización

`core.services.authorization` define acciones de producto:

- `EVENT_VIEW`
- `EVENT_EDIT`
- `EVENT_GUESTS`
- `EVENT_TABLES`
- `EVENT_BUILDER`
- `EVENT_OPERATIONS`
- `CLIENT_PORTAL`
- `PROVIDER_PORTAL`

`eventos_visibles_usuario()` es útil para selección/navegación, pero una operación sensible debe validar `usuario_puede_evento(..., action)`.

## 4. Dashboards V3

### Empresa
Administra negocio/recursos maestros y abre eventos. No duplica operación interna de cada evento.

### Planner
Bandeja de coordinación: trabajo Cliente/Proveedor/Interno, eventos y agenda. La operación detallada vive en Event Dashboard/Service Workspace.

### Event Dashboard
Centro de operación interna del evento.

### Cliente
Solo información/acciones propias: servicios cliente, agenda pertinente, tareas propias, documentos compartidos, pagos a empresa, invitados/RSVP y compartir invitaciones.

### Proveedor
Solo sus servicios, cotizaciones, agenda/tareas propias, documentos compartidos, pagos Empresa→Proveedor y canal Planner↔Proveedor.

## 5. Collaboration Workspace

Canales:

```text
CLIENTE_PLANNER
PLANNER_PROVEEDOR
INTERNO
```

Cliente no recibe cotizaciones/costos internos del proveedor. Proveedor no recibe información financiera/comercial del cliente.

Planner/Empresa puede limpiar mensajes/referencias con auditoría. Decisiones/cotizaciones/propuestas/aprobaciones estructuradas sobreviven a la limpieza del chat.

## 6. Finanzas

### Ingreso reportado por cliente
`PagoClienteEvento`.

Receptor y validador: Empresa/Planner.

### Compromiso/egreso operativo
`GastoEvento` + `PagoEvento`.

Destino: proveedor/operación.

No se mezclan ambos flujos.

## 7. Invitados

`Invitado` es la autoridad individual de RSVP. `Grupoinvitacion` conserva el UUID y los datos de compartir.

La capacidad contratada se valida antes de crear lugares desde Portal Cliente.

## 8. Builder

DIRTEC Builder está funcionalmente congelado en este baseline.

- no se refactoriza para plantillas;
- no se duplica para Cliente;
- su acceso requiere `EVENT_BUILDER`;
- futuras capacidades/paquetes decidirán quién puede entrar antes de invocar el mismo Builder.

## 9. Archivos

Media pública de invitaciones puede servirse directamente.

Documentos, comprobantes, cotizaciones, adjuntos de colaboración y evidencias privadas se entregan mediante `/secure/...` con autorización Django. El reverse proxy bloquea acceso directo a sus prefijos físicos dentro de `/media/`.

## 10. Producción

```text
Hostinger DNS
   ↓
Caddy :443
   ↓
Waitress 127.0.0.1:8001
   ↓
Django
   ↓
PostgreSQL 127.0.0.1:5432
```

No exponer 8001 ni 5432 al Internet.

## 11. Desarrollo futuro

Después del baseline productivo:

1. capacidades/entitlements de paquete;
2. motor de plantillas genéricas independiente;
3. acceso Builder por paquete;
4. eliminación física gradual de modelos legacy restantes.

Estas funciones se desarrollan fuera de la copia que sirve producción y se incorporan mediante releases posteriores.
