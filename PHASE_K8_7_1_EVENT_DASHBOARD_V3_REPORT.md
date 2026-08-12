# K.8.7.1 — Event Dashboard V3

## Objetivo
Reorganizar el dashboard del evento alrededor del dominio Event-Centric ya construido, sin crear modelos nuevos ni tocar el Builder.

## Jerarquía principal
Resumen → Servicios → Agenda → Tareas → Finanzas → Documentos → Invitados → Invitación → Equipo.

## Decisiones
- `ServicioEvento` reemplaza en navegación principal los silos Banquete/Decoración/Música.
- Agenda, tareas, documentos y gastos reutilizan sus modelos existentes y su FK opcional a `ServicioEvento` de K.8.6.
- Finanzas separa contrato/extras del cliente de costos/pagos operativos.
- Invitados y Mesas siguen como dominios especializados.
- Builder permanece aislado; el dashboard solo enlaza a él.
- Contenido y Operación legacy siguen disponibles bajo “Compatibilidad temporal”; no se borran aún.
- No hay migraciones en K.8.7.1.

## Código modular
`eventos/dashboard_v3.py` concentra queries/métricas V3 para evitar seguir aumentando la responsabilidad visual de `invitaciones/views.py`.

## Siguiente paso
Después del gate manual: K.8.7.2 Planner Dashboard V3, utilizando el Evento V3 como destino operativo en lugar de duplicar la operación.
