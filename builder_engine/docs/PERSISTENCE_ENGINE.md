# Persistence Engine

Versión del contrato: 1

El módulo `persistence` centraliza carga, guardado, autosave y publicación sin introducir rutas del backend dentro del Core.

## PersistencePort

El host debe inyectar:

- `load(context)`
- `save({ document, reason, context })`
- `publish({ document, context })`

## Autosave

El autosave usa debounce configurable. Cada cambio del Documento agenda un guardado. Los cambios provenientes de carga o replay del historial no generan autosave adicional.

## Dirty state

`BuilderApp` conserva el estado `dirty`. El servicio llama `markSaved()` después de un guardado correcto.

## WorkspaceState

El estado de interfaz se mantiene separado del Documento publicado:

- selección
- zoom
- pestañas
- scrolls
- acordeones
- dispositivo de preview

## Django

El adaptador Django recibe URLs y CSRF desde el host. No contiene rutas concretas.
