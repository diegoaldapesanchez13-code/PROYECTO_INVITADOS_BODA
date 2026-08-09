# PHASE E.3 — Python Source Purge

## Método

Se construyó un grafo de llamadas de `invitaciones/views.py`.

Las raíces activas se tomaron de las referencias reales a `views.*` del proyecto.
La subred originada únicamente en las rutas legacy retiradas en E.2 fue candidata
a eliminación.

Luego se aplicó un segundo fixed-point de seguridad: si cualquier función
conservada llama a una candidata, esa función y sus dependencias se conservan.

## Resultado

```text
subred legacy analizada: 80 funciones
funciones purgadas: 52
helpers compartidos preservados: 28

views.py antes: 6877 líneas
views.py después: 4785 líneas
reducción: 2092 líneas

bytes antes: 314361
bytes después: 215595
reducción: 98766 bytes
```

## Helpers legacy/shared preservados

- `aplicar_estructura_plantilla_evento`
- `aplicar_plantilla_evento`
- `archivo_pasa_validadores`
- `bool_post`
- `construir_configuracion_diseno`
- `contenido_editor_payload`
- `convertir_decimal`
- `convertir_entero`
- `crear_invitados_desde_textarea`
- `datos_default_seccion`
- `editor_invitacion_visual`
- `invitados_editor_payload`
- `limpiar_texto`
- `mesa_actual_grupo`
- `mesa_actual_invitado`
- `mesas_editor_payload`
- `obtener_diseno_invitacion`
- `qr_url_para_link`
- `serializar_grupo_editor`
- `serializar_invitado_editor`
- `serializar_itinerario_editor`
- `serializar_persona_editor`
- `serializar_regalo_editor`
- `serializar_seccion_editor`
- `serializar_version_editor`
- `sincronizar_diseno_con_secciones`
- `sincronizar_secciones_invitacion`
- `versiones_editor_payload`

No se cambian URLs, modelos, migraciones, Builder, Renderer, Assets ni RSVP.
