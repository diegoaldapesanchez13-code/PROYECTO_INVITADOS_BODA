# Sprint 10.2 — Montaje visual de BuilderApp

## Resultado

Se crea una ruta paralela del editor oficial:

```text
/dashboard/editor-invitacion/<evento_id>/engine/
```

La ruta anterior permanece disponible como respaldo.

## Flujo

1. Django renderiza el shell y endpoints.
2. `editor_bootstrap.js` crea `BuilderApp`.
3. Se registra `PersistenceModule`.
4. El Documento se carga desde Django.
5. Guardar, autosave, recargar y publicar usan Persistence Contract v1.
6. El objeto temporal `window.DIRTEC_BUILDER` permite diagnóstico.

## Build estático

El código fuente sigue viviendo en:

```text
builder_engine/frontend/
```

Para servirlo con Django se ejecuta:

```powershell
python builder_engine/build/build_static.py
```

El build se copia a:

```text
invitaciones/static/invitaciones/builder_engine/
```

El directorio de destino es artefacto de ejecución; la fuente oficial continúa siendo `builder_engine/frontend`.
