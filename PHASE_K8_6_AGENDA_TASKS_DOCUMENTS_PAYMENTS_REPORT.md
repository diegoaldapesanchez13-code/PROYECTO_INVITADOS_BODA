# K.8.6 — Agenda / Tasks / Documents / Payments Linking

## Objetivo
Relacionar los módulos operativos existentes con `ServicioEvento` sin crear modelos duplicados ni mezclar privacidad financiera con colaboración.

## Decisión arquitectónica
Se reutilizan los modelos existentes:

- `TareaEvento`
- `ActividadItinerario`
- `DocumentoEvento`
- `GastoEvento`
- `PagoEvento`

Se agrega FK opcional `servicio_evento` a los primeros cuatro. `PagoEvento` NO recibe una FK duplicada: su servicio se deriva de `pago.gasto.servicio_evento`.

## Relaciones finales

```text
ServicioEvento
├── tareas_operativas -> TareaEvento
├── actividades_agenda -> ActividadItinerario
├── documentos_operativos -> DocumentoEvento
└── gastos_operativos -> GastoEvento
    └── pagos -> PagoEvento
```

## Compatibilidad
Los nuevos FK son `null=True, blank=True` y `SET_NULL`. Los registros legacy siguen funcionando sin servicio asociado. No existe backfill automático porque inferir relaciones por nombre/proveedor sería inseguro.

## Operación desde workspace
El Planner/equipo operativo puede:

- crear tareas vinculadas;
- crear citas/actividades vinculadas;
- subir documentos vinculados;
- crear gastos vinculados;
- registrar pagos en gastos del servicio;
- vincular registros preexistentes del mismo evento;
- desvincular sin eliminar el registro fuente.

## Visibilidad
- Operador: toda la operación, incluidas finanzas.
- Cliente: citas relacionadas, documentos `visible_cliente=True` y tareas asignadas a su usuario.
- Proveedor: citas relacionadas con su proveedor.
- Cliente/proveedor: nunca reciben el bloque financiero del servicio.

## Integridad
Los modelos vinculables validan que `servicio_evento.evento_id == evento_id`. `GastoEvento` valida además el proveedor cuando ambas relaciones están presentes.

## Migraciones
- `tareas.0004_servicio_evento_k86`
- `itinerario.0002_servicio_evento_k86`
- `documentos.0003_servicio_evento_k86`
- `presupuesto.0003_servicio_evento_k86`

## Fuera de alcance
- Rediseño general de dashboards (K.8.7).
- Eliminación de CRUD legacy.
- Conversión automática de texto de chat a fechas/tareas mediante IA.
- Limpieza final de modelos legacy (K.8.10).
- Builder de invitaciones.
