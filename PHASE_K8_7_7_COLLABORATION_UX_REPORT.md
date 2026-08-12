# K.8.7.7 — Collaboration UX & Planner Cleanup Tools

## Objetivo
Hacer más amigable la experiencia de mensajería compartida por Cliente, Planner y Proveedor y añadir herramientas de limpieza exclusivas del equipo operativo.

## Chat UX
- mensajes propios visualmente diferenciados;
- descripción contextual por canal;
- contador de mensajes;
- composer más claro;
- selector de tema con lenguaje amigable;
- adjuntos conservan miniaturas;
- auto-scroll al último mensaje;
- Ctrl/Cmd + Enter envía;
- referencias y temas con controles más claros.

## Herramientas Planner/Empresa
- eliminar mensaje individual;
- vaciar historial del canal actual;
- eliminar referencia;
- archivar tema;
- eliminar adjuntos continúa disponible.

## Reglas destructivas
### Eliminar mensaje
Solo equipo operativo.
Si contiene un adjunto promovido a Referencia, se bloquea hasta retirar la referencia.

### Vaciar historial
Solo equipo operativo.
Afecta únicamente el canal seleccionado.
Elimina:
- mensajes del canal;
- adjuntos de esos mensajes;
- referencias originadas en esos mensajes.

Conserva:
- DecisionServicio;
- CotizacionServicio;
- PropuestaServicioCliente;
- AprobacionServicio.

Los vínculos `mensaje_origen` quedan `NULL` cuando corresponde.

### Referencias
Eliminar una referencia no elimina automáticamente el mensaje/archivo original.

### Temas
Se archivan (`activo=False`) en lugar de borrar, para no destruir contexto histórico.

## Roles externos
Cliente y Proveedor:
- pueden conversar en sus canales autorizados;
- pueden eliminar sus propios adjuntos conforme a reglas existentes;
- NO pueden eliminar mensajes completos;
- NO pueden vaciar historial;
- NO pueden eliminar referencias;
- NO pueden archivar temas.

## Migraciones
No requiere migraciones.

## Builder
No se modifica.
