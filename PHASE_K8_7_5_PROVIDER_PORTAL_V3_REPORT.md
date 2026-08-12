# K.8.7.5 — Provider Portal V3

## Objetivo
Sustituir el Portal Proveedor legacy por una experiencia Event-Centric centrada en `ServicioEvento`.

## Navegación
- Inicio
- Servicios
- Cotizaciones
- Agenda
- Tareas
- Documentos
- Pagos

## Retiro del flujo legacy
El Portal Proveedor deja de usar:
- `ExpedienteServicio`;
- bloque `_proveedor.html`;
- formulario paralelo `estado_proveedor / Respuesta operativa`;
- endpoint `actualizar_servicio_proveedor`.

Las rutas/modelos legacy restantes se revisarán en la auditoría global posterior.

## Cotizaciones
Se reutiliza `CotizacionServicio` versionada.
El proveedor puede enviar nuevas versiones.
El Planner sigue siendo el único que acepta, rechaza o solicita cambios.

## Agenda y tareas
- Citas: solo cuando el proveedor es participante.
- Actividades: solo las ligadas a su proveedor/ServicioEvento.
- Tareas: solo las asignadas al usuario proveedor y ligadas a sus servicios.

## Documentos
Se agrega `DocumentoEvento.visible_proveedor`.
Regla:
- Planner/Empresa decide qué documento compartir con proveedor.
- Proveedor ve documentos `visible_proveedor=True`.
- También ve archivos que él mismo subió.
- Un archivo subido por proveedor queda `visible_cliente=False` por defecto.

## Pagos
La sección Pagos consume exclusivamente:
`Empresa -> GastoEvento -> PagoEvento -> Proveedor`

No consume ni expone `PagoClienteEvento`.
Tampoco muestra `valor_contratado`, `cargo_adicional_cliente`, margen o precio comercial del cliente.

## Builder
No se modifica.

## Migración
`documentos.0004_visible_proveedor_k875`
