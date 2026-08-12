# K.8.4 — Service Workspace & Structured Communication

## Objetivo
Consolidar la comunicación nueva directamente alrededor de `ServicioEvento`, sin depender de `ExpedienteServicio` como segundo núcleo operativo y sin tocar el Builder.

## Nuevo dominio
- `TemaServicio`: temas contextuales dentro del servicio (Menú, Bebidas, Trasnochado, Mantelería, etc.).
- `ConversacionServicio`: una conversación por servicio/canal.
- Canales: `CLIENTE_PLANNER`, `PLANNER_PROVEEDOR`, `INTERNO`.
- `MensajeServicio`: texto asociado opcionalmente a un tema.
- `AdjuntoMensajeServicio`: múltiples archivos por mensaje.
- `ReferenciaServicio`: permite promover un adjunto a referencia persistente del servicio.

## Regla de diseño
No existe un chat por cada tema. Hay una conversación por canal y servicio; los temas contextualizan mensajes. Esto evita fragmentación excesiva.

## Seguridad
- Planner/operación: ve los tres canales.
- Cliente del evento: solo `CLIENTE_PLANNER`.
- Proveedor asignado al servicio: solo `PLANNER_PROVEEDOR`.
- `INTERNO` nunca se muestra a cliente/proveedor.
- Usuario ajeno al evento/servicio: 403.

## Compatibilidad legacy
`ExpedienteServicio`, `MensajeExpediente`, cotizaciones y propuestas siguen existiendo por compatibilidad.
La migración `0003_migrate_legacy_messages_k84` copia los mensajes/adjuntos legacy ligados a un `ServicioEvento` al workspace nuevo sin borrar el historial original.
Cotizaciones y propuestas se consolidarán en la fase posterior.

## UI
Se agrega un workspace responsive en:
`/colaboracion/servicios/<id>/workspace/`

Se agregan accesos desde:
- directorio de servicios del Planner;
- operación del evento;
- portal de proveedor;
- tarjetas legacy de colaboración cuando ya existe `ServicioEvento`.

## Gates ejecutados
- `manage.py check`: OK
- `makemigrations --check`: OK
- migración sobre copia SQLite baseline: OK
- 32 tests de regresión/domain: OK
- 7/7 tests específicos K.8.4: OK

## Fuera de alcance
- decisiones/aprobaciones estructuradas;
- versionado nuevo de cotizaciones/propuestas;
- conversión de mensajes a pagos/citas/tareas;
- eliminación de modelos legacy;
- Builder.
