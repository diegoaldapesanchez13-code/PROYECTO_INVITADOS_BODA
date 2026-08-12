# K.5.1 — Operations Layout + Agenda

## Operations layout

The two-column operation layout no longer forces large edit forms into a
compressed right column.

- Wide desktop: create + records side by side.
- <= 1280 px: stack vertically.
- Every field uses the available container width.
- File inputs cannot force horizontal overflow.
- Open edit cards use responsive auto-fit grids.
- Mobile falls to one column.

This applies to every Operation subpanel because the correction is made in the
shared operation layout.

## Task agenda

TareaEvento now supports:
- fecha_inicio
- hora_inicio (optional)
- fecha_limite / fin
- hora_fin (optional)

Existing date-only tasks remain valid and render as all-day calendar items.

A task with time becomes an agenda appointment. FullCalendar now defaults to
week time-grid on desktop and exposes:
- Month
- Week
- Day
- Agenda/list

The calendar displays a current-time indicator and 30-minute slots.
