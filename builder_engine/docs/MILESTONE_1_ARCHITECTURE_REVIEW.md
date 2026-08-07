# Milestone 1 — Revisión de arquitectura

**Proyecto:** DIRTEC Event Studio  
**Motor:** DIRTEC Builder Engine  
**Rama revisada:** `builder-r3`  
**Versión revisada:** `0.11.0`  
**Estado:** Aprobado con ajustes obligatorios antes de integrar Django

## 1. Alcance revisado

La revisión cubre los módulos actualmente extraídos al Engine:

- Kernel (`BuilderApp` y `BuilderRegistry`)
- Document Engine
- Canvas Module
- Inspector Module
- Universal Renderer
- Assets Module
- History Engine
- SDK mínimo
- Manifest y versionado

No se revisa todavía la integración activa con Django, porque aún no debe existir en el Engine oficial.

## 2. Resultado general

La arquitectura es suficientemente sólida para continuar la extracción modular. El Engine ya tiene una separación correcta entre:

1. Documento
2. Servicios de dominio visual
3. Módulos registrables
4. Adaptadores temporales de R3
5. Integraciones futuras

No se recomienda conectar Django todavía. Primero deben extraerse `Components`, `Interaction` y `Persistence`, porque son contratos centrales que la integración Django necesitará.

## 3. Fortalezas confirmadas

### Kernel desacoplado

`BuilderApp` coordina el Documento y módulos registrados sin conocer Canvas, Renderer, Django o el negocio de eventos.

### Documento como contrato único

El Documento ya contiene:

- metadata
- theme
- assets
- globals
- canvases

Esto permite usar el mismo origen en edición, preview y publicación.

### Módulos sin DOM ni backend

Canvas, Inspector, Assets e History trabajan sobre el Documento y no dependen de templates Django.

### Renderer universal

El Renderer está planteado para operar en modos:

- EDIT
- PREVIEW
- PUBLIC

No debe crearse otro renderer para la invitación pública.

### Assets persistentes

El Documento conserva referencias y metadatos, no bytes, Base64 ni URLs `blob:`.

### History transaccional

El historial puede consolidar arrastres y escritura consecutiva sin guardar cientos de pasos.

## 4. Ajustes obligatorios

### A-01 — Orden determinista de módulos

El arranque actual depende del orden de registro. Antes de integrar Django debe existir prioridad o dependencias declaradas.

Orden recomendado:

1. document
2. history
3. assets
4. canvas
5. components
6. interaction
7. inspector
8. renderer
9. persistence
10. host integration

### A-02 — Contrato estándar de módulos

Todos los módulos deben exponer la misma forma:

```js
{
  key,
  version,
  dependencies,
  start(context),
  destroy(context)
}
```

Esto permitirá validar dependencias y compatibilidad antes del arranque.

### A-03 — Actualizaciones siempre por comandos

Canvas, Inspector y futuros módulos no deben modificar el Documento por rutas independientes sin metadatos uniformes.

Todo cambio debe aportar:

- `label`
- `source`
- `mergeKey`
- `transactionId` cuando aplique

History y autosave dependerán de esos metadatos.

### A-04 — Separar estado persistente de estado de interfaz

No deben guardarse en el Documento público:

- pestaña activa del Inspector
- scroll de paneles
- acordeones abiertos
- zoom del editor
- selección actual
- marco móvil seleccionado

Ese estado debe vivir en `workspaceState` local o en preferencias del usuario, no en la invitación publicada.

### A-05 — Congelar nombres del esquema antes de Django

Antes de persistir documentos reales debe decidirse definitivamente:

- `canvases`
- `nodes`
- `globals`
- `assets`
- `theme`
- `metadata`

Después de conectar Django, cualquier cambio requerirá migradores de esquema.

### A-06 — SDK con validación de contratos

El SDK actual registra extensiones, pero todavía no valida la forma de componentes, renderers o inspectores.

Antes de aceptar plugins externos debe validar:

- ID único
- versión
- tipo
- factory
- renderer
- inspector
- defaults
- migraciones
- capacidades

### A-07 — No extraer backend dentro del Engine todavía

`builder_engine/backend/` no es necesario en el Milestone 1. Django debe seguir siendo el backend del SaaS mediante un adaptador.

El Engine debe permanecer frontend y agnóstico al servidor.

## 5. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---:|---|
| Conectar Django antes de congelar el esquema | Alto | Extraer Components, Interaction y Persistence primero |
| Duplicar estado entre `builder_v3`, `static/js/builder` y `builder_engine` | Alto | Definir una única fuente oficial y usar adaptadores temporales |
| Guardar estado de UI dentro del Documento | Medio | Crear `WorkspaceState` separado |
| Dependencia implícita del orden de registro | Medio | Añadir dependencias y prioridad de módulos |
| Snapshots grandes en History | Medio futuro | Mantener límite; introducir patches después de estabilizar schema |
| SDK demasiado permisivo | Medio | Añadir validadores antes del sistema de plugins |

## 6. Qué se mantiene temporalmente

### `builder_v3`

Debe mantenerse hasta que:

- Components haya sido extraído;
- Interaction haya sido extraído;
- Renderer nuevo produzca equivalencia visual;
- Django cargue y guarde el Documento;
- la vista pública use el Renderer universal.

### `static/invitaciones/js/builder`

Debe considerarse una etapa intermedia. No debe convertirse en una tercera fuente permanente.

### Editor e invitación antiguos

Deben permanecer como respaldo hasta completar pruebas de:

- carga;
- guardado;
- recarga;
- publicación;
- UUID;
- RSVP;
- assets;
- preview;
- vista pública.

## 7. Próximo orden aprobado

### Sprint 7 — Components Engine

Extraer:

- Component Registry
- Component Factory
- contratos
- defaults
- capacidades
- blueprints compuestos
- adapters R3

### Sprint 8 — Interaction Engine

Extraer:

- acciones
- ejecutores
- validadores
- navegación
- Maps
- WhatsApp
- URL
- eventos de componentes

### Sprint 9 — Persistence Engine

Crear:

- serializer definitivo
- autosave
- dirty state
- load/save/publish ports
- adaptador Django sin rutas en el Core

### Sprint 10 — Integración Django

Entonces sí:

- montar BuilderApp en la plantilla real;
- cargar documento;
- guardar borrador;
- recuperar documento;
- subir assets persistentes.

## 8. Decisión final

**La arquitectura queda aprobada para continuar.**

No se aprueba todavía conectar Django ni eliminar el sistema antiguo.

El siguiente sprint oficial es:

> **Sprint 7 — Components Engine**

