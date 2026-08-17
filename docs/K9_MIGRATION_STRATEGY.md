# K9 Migration Strategy

Estado: estrategia aditiva. No ejecutar migraciones en K9.0.

## Reglas de compatibilidad

- No borrar modelos actuales.
- No renombrar tablas actuales.
- No renombrar `EventoBoda`.
- No renombrar `PaqueteBoda`.
- No renombrar `WEDDING_PLANNER` ni `wedding_planner`.
- No hacer reemplazos globales.
- No romper snapshots/materializacion K8.
- Cada transicion debe estar cubierta por tests antes de activar UI productiva.

## Estrategia general

1. Agregar modelos/campos nuevos.
2. Agregar services/adapters que lean K8 y K9.
3. Crear tests de compatibilidad.
4. Poblar datos opcionalmente con data migrations reversibles o comandos offline.
5. Activar UI por fases.
6. Deprecar legacy solo cuando no haya dependencias vivas.

## Catalogo

Fase implementada: K9.2.

Crear app nueva `catalogo/` es la alternativa preferida por bajo acoplamiento y mejor testabilidad.

Alternativas:

- A) `catalogo/`: clara, pequena, reusable por empresa, evita mezclar costo proveedor con descripcion comercial. Riesgo: nuevos imports y migraciones.
- B) extender `proveedores`: menos archivos nuevos, pero refuerza el error conceptual de que el servicio pertenece al proveedor.
- C) app `servicios/`: semanticamente amplia, pero puede confundirse con `ServicioEvento`.

Decision aplicada: `catalogo/`.

Modelos implementados:

- `ServicioCatalogo`;
- `ServicioCatalogoArchivo`;
- media opcional validada con los validadores existentes y almacenada fuera de `MEDIA_ROOT`;
- admin por empresa;
- constraint `empresa` + `nombre` y validacion case-insensitive en `clean()`;
- permisos por tenant usando `Actions.COMPANY_MANAGE_CATALOGS`;
- migracion aditiva `catalogo/migrations/0001_initial.py`.

Decision R2: como K9.2 aun no esta versionada ni desplegada, la migracion local `0001_initial.py` se mantiene limpia e incluye el storage privado de catalogo desde el inicio. No se crea `0002` y no se alteran migraciones K8.

Storage R2:

- `PRIVATE_MEDIA_ROOT` separado fisicamente de `MEDIA_ROOT`;
- sin `PRIVATE_MEDIA_URL`;
- `ServicioCatalogo.imagen_principal` y `ServicioCatalogoArchivo.archivo` usan `PrivateCatalogoStorage`;
- Caddy/Nginx futuro no debe servir `PRIVATE_MEDIA_ROOT`;
- las vistas Django autorizadas son la unica puerta de acceso.

## Puente catalogo-proveedor

Fase implementada: K9.3.

No eliminar `ServicioCatalogoProveedor`. Usarlo como legacy/adaptador.

Modelo puente implementado en `catalogo/`:

- `servicio_catalogo`;
- `proveedor`;
- activo;
- notas;
- timestamps.

Decision K9.3: no agregar costo/precio al puente. La relacion expresa que el proveedor puede prestar el servicio; costos reales siguen en operacion/evento posterior.

Tenant:

- `proveedor.empresa` debe existir;
- `proveedor.empresa` debe coincidir con `servicio_catalogo.empresa`;
- constraint unico `proveedor` + `servicio_catalogo`.

Migracion de datos:

No se ejecuta migracion masiva desde `ServicioCatalogoProveedor` en K9.3. La convivencia K8/K9 queda testeada: legacy sigue funcionando y `ServicioEvento.servicio_catalogo` no cambia.

## Paquetes

Fase implementada: K9.4.

Campos aditivos agregados a `PaqueteBoda`:

- `precio_adulto`;
- `precio_nino`;
- `cargo_fijo`;
- `capacidad_minima_recomendada`;
- `capacidad_maxima_recomendada`;
- `duracion_evento`;
- `portada`;
- `pdf_comercial`.

No retirar:

- `precio_base`;
- `numero_personas_incluidas`;
- `ServicioPaquete`.

Compatibilidad:

- Si paquete es v1, calcular con `precio_base`/`precio_acordado`.
- Si paquete es v2, calcular con adulto/nino/cargo fijo.
- Vistas legacy siguen leyendo campos v1 hasta su fase.
- Media comercial usa storage privado compartido con catalogo K9.2.
- Migracion aditiva creada: `paquetes/migrations/0004_paqueteboda_capacidad_maxima_recomendada_and_more.py`.

## Servicios del paquete

Fase implementada en alcance comercial K9.4.

Modelo `PaqueteServicio` aditivo creado con FK a `ServicioCatalogo`.

Plan seguro:

1. Agregar modelo nuevo `PaqueteServicio`.
2. Mantener `ServicioPaquete`.
3. Emitir lineas normalizadas desde ambos en el DTO comercial.
4. No ejecutar migracion masiva de datos legacy en K9.4.
5. Materializacion v2 queda pendiente para K9.6.
6. Lectores v1 siguen con `ServicioPaquete`.

Evitar duplicados:

- usar clave origen estable;
- conservar `paquete_evento` y origen legacy;
- en v2 usar constraint por contrato/linea_origen si se agrega modelo intermedio.

## Snapshot v1 -> v2

Actual:

- `PaqueteEvento.snapshot_paquete` v1.
- `MATERIALIZACION_VERSION = 1`.
- `materializacion_version` en `PaqueteEvento`.

Objetivo:

- v1 legacy K8: reconstruible siempre.
- v2 K9: snapshot comercial del contrato completo.

Ubicacion recomendada:

- `ContratoEvento.snapshot_comercial` para el contrato aceptado;
- campo `snapshot_version` aditivo si se requiere;
- conservar `PaqueteEvento.snapshot_paquete` para K8.

Contenido v2:

- `version`: 2;
- paquete snapshot;
- sede snapshot;
- adultos/ninos;
- tarifas adulto/nino/cargo fijo;
- incluidos;
- adicionales;
- cortesias;
- descuentos;
- total;
- condiciones;
- lineas con origen y claves estables;
- metadata de calculo.

Lectores:

- `leer_contrato_publico(snapshot)` soporta v1/v2.
- `leer_contrato_interno(snapshot)` soporta v1/v2.
- Nunca modificar snapshot firmado salvo crear nueva version de contrato.

## Materializacion v2

Fase recomendada: K9.6.

Preservar de v1:

- snapshot contractual;
- idempotencia;
- no duplicar `ServicioEvento`;
- conservar datos aunque desaparezca master;
- `precio_incluido`/valor comercial hacia `valor_contratado`;
- costo proveedor inicia separado.

Evolucion:

- `MATERIALIZACION_VERSION = 2` cuando exista snapshot K9.
- Materializar incluidos, adicionales y cortesias.
- `CORTESIA` con `cargo_adicional_cliente = 0`.
- Adicionales con snapshot de tarifa.
- Servicios sin proveedor permitido.
- Prestacion por definir o interna sin proveedor ficticio.

## Proveedor post-contrato

Fase recomendada: K9.6-K9.7.

`ServicioEvento.proveedor` ya acepta `null`.

Agregar solo si hace falta:

- `prestacion_tipo`: `EMPRESA`, `PROVEEDOR`, `POR_DEFINIR`.
- `proveedor_asignado_en`;
- `proveedor_asignado_por`.

Reglas:

- Asignar proveedor no cambia `valor_contratado`.
- Cambiar `costo_proveedor` o `GastoEvento` no cambia contrato.
- Proveedor solo ve servicios asignados a el.

## Finanzas

Fase recomendada: K9.7.

No crear segundo sistema.

Adaptaciones:

- `ContratoEvento` o service financiero calcula monto contratado/saldo cliente desde snapshot.
- `PagoClienteEvento` aplica contra evento/contrato, no contra proveedor.
- `GastoEvento` registra costo operativo, con `servicio_evento` opcional.
- `PagoEvento` registra pagos de empresa a costos/proveedores.

Reportes:

- ingreso contratado;
- pagos cliente recibidos;
- saldo cliente;
- costos estimados/reales;
- pagos operativos;
- saldo proveedor/costo;
- margen interno solo para Empresa/Planner autorizado/DIRTEC.

## CRUD operativo

Fase recomendada: K9.8.

Auditoria actual:

- servicios, tareas, gastos, pagos y documentos tienen crear/editar/eliminar en dashboard legacy;
- workspace tiene eliminar/limpiar/archivar en mensajes/temas/referencias;
- citas viven en `ActividadItinerario`;
- varias eliminaciones son fisicas y tambien borran archivos.

Estrategia:

- distinguir crear/editar/eliminar/cancelar/archivar por entidad;
- preferir `cancelar` o `archivar` cuando haya historial contractual/operativo;
- mantener hard delete solo para errores de captura antes de contrato o datos sin auditoria requerida;
- definir permisos por `Actions.EVENT_OPERATIONS`, cliente/proveedor y autor/responsable.

## Login/logout

Fase recomendada: K9.1.

Actual:

- `LoginCentralView` hereda `LoginView`.
- `LOGIN_REDIRECT_URL = /redirigir/`.
- `LogoutView(next_page='login')`.
- No se observo override de `get_success_url` que valide `next` contra el usuario autenticado.

Politica objetivo:

- logout -> login neutral;
- login -> dashboard por rol;
- `next` solo si el usuario nuevo esta autorizado para ese destino.

Implementacion futura:

- descartar `next` por defecto tras logout;
- validar `next` con resolved view + objeto o endpoint permitido;
- si falla, redirigir a `/redirigir/`;
- limpiar contexto de tenant/evento en sesion si existe.

## Landing, terminologia y branding

Fase recomendada: K9.9.

Landing actual es legacy visible. Cambios futuros solo visibles, sin renombres internos automaticos.

Terminologia:

- clasificar apariciones como visible, codigo, modelo, URL, migracion, test o documentacion;
- cambiar copy visible primero;
- nombres internos requieren estrategia de migracion.

Branding multiempresa:

- usar `EmpresaSuscriptora.logotipo` y `colores_marca`;
- agregar portada/hero/control de encabezados si se aprueba;
- no permitir CSS arbitrario.

## Builder mobile

Fase recomendada: K9.10.

No modificar Builder en K9.0.

Objetivo:

- conservar desktop actual;
- mobile con canvas principal;
- assets/layers/inspector como drawer o bottom sheet;
- toolbar tactil;
- `safe-area`;
- `100dvh`;
- sin overflow horizontal;
- shortcuts sin interceptar inputs/textarea/select/contenteditable.
