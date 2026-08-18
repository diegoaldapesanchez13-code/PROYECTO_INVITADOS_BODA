# K9 Domain Model

Estado: borrador conceptual. No implementar sin aprobacion K9.1+.

## Principios contractuales

1. CATALOGO DESCRIBE.
2. PAQUETE VENDE.
3. EVENTO DEFINE CANTIDADES.
4. PROVEEDOR DEFINE COSTO OPERATIVO POSTERIORMENTE.
5. CONTRATO CONGELA EL ACUERDO.
6. SERVICIOEVENTO ES LA INSTANCIA OPERATIVA.
7. PRESUPUESTO REGISTRA COSTOS Y PAGOS.
8. COLABORACION OPERA SOBRE SERVICIOEVENTO.

Version corta solicitada:

- CATALOGO DESCRIBE.
- PAQUETE VENDE.
- EVENTO DEFINE CANTIDADES.
- PROVEEDOR CUESTA DESPUES.
- CONTRATO CONGELA.
- SERVICIOEVENTO EJECUTA.
- PRESUPUESTO REGISTRA.
- COLABORACION OPERA.

## Dominio actual relevante

### Tenant y evento

- `EmpresaSuscriptora` ya es el limite natural de catalogos, sedes, proveedores, paquetes, usuarios y eventos.
- `SedeEvento` ya pertenece a empresa y tiene capacidad/precio base.
- `EventoBoda` sigue siendo el evento real actual. Tiene `empresa`, `sede`, `tipo_evento`, `estado`, `wedding_planner`, `clientes`, estimado/capacidad/precio por persona y muchos campos de invitacion.
- `DetalleProduccionEvento` contiene datos de contrato/produccion legacy: folio, adultos, ninos, horas, renta, anticipos, saldo y condiciones.
- `ParticipanteEvento` agrega roles por evento, incluyendo cliente, planner y colaborador.

### Paquetes

- `PaqueteBoda`: empresa nullable, nombre, descripcion, precio base, numero de personas incluidas, activo.
- `ServicioPaquete`: paquete, tipo de servicio enum, descripcion, cantidad, precio incluido.
- `PaqueteEvento`: evento, paquete, precio acordado, servicios adicionales texto, descuento, total, estado, notas, `snapshot_paquete`, `materializado_en`, `materializacion_version`.
- `paquetes/services.py` ya resuelve snapshot, bloqueo transaccional e idempotencia.

### Proveedores y servicios

- `Proveedor`: empresa nullable, usuario, razon/nombre comercial, `tipo_proveedor`, etiquetas/logistica/datos privados, activo.
- `EtiquetaProveedor`: taxonomia por empresa.
- `ServicioCatalogoProveedor`: catalogo dependiente de proveedor con costo/precio de referencia.
- `ServicioEvento`: evento, proveedor nullable, servicio catalogo nullable, paquete evento/origen, origen, modalidad, estados, descripcion, cantidades, valores comerciales, costos, archivos, notas y snapshots.

### Finanzas

- `GastoEvento`: costo operativo por evento, opcionalmente asociado a `ServicioEvento`.
- `PagoEvento`: pago empresa/proveedor/costo operativo contra `GastoEvento`.
- `PagoClienteEvento`: pago reportado por cliente a empresa, opcionalmente asociado a `ServicioEvento` solo como concepto.

### Colaboracion

- Workspace K8 opera sobre `ServicioEvento`.
- Canales actuales: `CLIENTE_PLANNER`, `PLANNER_PROVEEDOR`, `INTERNO`.
- No se requiere chat nuevo para K9.

## Catalogo general de servicios

Objetivo: cada `EmpresaSuscriptora` tendra su propio catalogo maestro que representa que existe, no cuanto cuesta.

Modelo implementado en K9.2: `catalogo.ServicioCatalogo`.

Campos actuales:

- `empresa`;
- `nombre`;
- `categoria`;
- `descripcion`;
- `unidad`;
- `activo`;
- `imagen_principal`;
- `created_at`;
- `updated_at`.

Archivos asociados implementados en K9.2: `catalogo.ServicioCatalogoArchivo`.

- `servicio`;
- `tipo` (`IMAGEN` o `PDF`);
- `archivo`;
- `titulo`;
- `orden`;
- `created_at`.

Regla: el catalogo general no debe exigir costo proveedor ni precio cliente.

Regla tenant: `empresa` se deriva del contexto de ruta validado; no se toma de POST. La desactivacion es logica con `activo=False`, sin borrado fisico.

Regla de media privada: `imagen_principal` y `ServicioCatalogoArchivo.archivo` usan storage privado bajo `PRIVATE_MEDIA_ROOT`; no se sirven por `MEDIA_URL`. El acceso ocurre solo mediante vistas autorizadas del modulo `catalogo/`.

Ejemplos: DJ de lujo, Banquete 2, Meseros, Capitan de meseros, Valet parking, Planta de luz, Decoracion floral, Mesa de postres, Alcohol, Coctel de bienvenida, Carpa, Manteleria, Letras Hollywood, Camara 360, Sala lounge, Trasnochado.

## Proveedores

Regla K9.3: un proveedor ofrece muchos servicios y un servicio puede tener muchos proveedores mediante `catalogo.ProveedorServicioCatalogo`.

`ProveedorServicioCatalogo` representa capacidad de prestacion, no precio ni asignacion a evento.

Campos actuales:

- `proveedor`;
- `servicio_catalogo`;
- `activo`;
- `notas`;
- `created_at`;
- `updated_at`.

Regla tenant: `proveedor.empresa` debe existir y coincidir con `servicio_catalogo.empresa`. Un proveedor legacy sin empresa no puede usar el catalogo K9 hasta corregir su tenant.

No eliminar aun:

- `Proveedor.tipo_proveedor`;
- `EtiquetaProveedor`;
- `ServicioCatalogoProveedor`.

Clasificacion K9.0:

- Reutilizable: `Proveedor`, `EtiquetaProveedor`, `ServicioEvento.proveedor` nullable, validaciones de tenant.
- Adaptable: `ServicioCatalogoProveedor` como fuente historica para migrar al puente catalogo-proveedor.
- Legacy a deprecar: `Proveedor.tipo_proveedor` como definicion principal de lo que ofrece.
- No tocar todavia: nombres `WEDDING_PLANNER`, `wedding_planner`, `visible_para_wedding_planners`.

K9.3 no migra automaticamente `ServicioCatalogoProveedor`; lo conserva como fuente historica legacy con costo/precio de referencia. `Proveedor.tipo_proveedor` sigue disponible como clasificacion legacy, pero no decide que servicios puede ofrecer el proveedor.

Prestacion futura en `ServicioEvento`:

- empresa interna;
- proveedor externo;
- por definir.

No crear proveedor ficticio para servicios internos. La asignacion de proveedor ocurre despues del contrato y solo afecta operacion/costos.

## Paquetes comerciales

El paquete vende una oferta, no ejecuta operacion.

Campos K9.4 implementados de forma aditiva en `PaqueteBoda`:

- empresa;
- nombre;
- descripcion;
- precio_adulto;
- precio_nino;
- cargo_fijo opcional;
- capacidad_minima_recomendada;
- capacidad_maxima_recomendada;
- duracion_evento;
- portada;
- media comercial asociada mediante `PaqueteMediaComercial`;
- pdf_comercial;
- activo;

Capacidad debe iniciar como advertencia/recomendacion, no bloqueo duro.

Formula base objetivo:

```text
base = adultos * precio_adulto + ninos * precio_nino + cargo_fijo
```

Decision K9.4 sobre tarifa infantil: si una propuesta tiene ninos y el paquete no tiene `precio_nino`, el motor genera advertencia explicita y no inventa `precio_nino = precio_adulto`.

Compatibilidad: si un paquete no usa tarifas K9, el motor puede leer `precio_base` como paquete legacy y emite advertencia de compatibilidad.

Portada, PDF comercial y media de paquete usan storage privado bajo `PRIVATE_MEDIA_ROOT`; no se sirven por `MEDIA_URL`.

## Servicios del paquete

Actual legacy: `ServicioPaquete(tipo_servicio, descripcion, cantidad, precio_incluido)`.

Implementado K9.4: `PaqueteServicio`.

Campos:

- `paquete`;
- `servicio_catalogo`;
- `cantidad`;
- `orden`;
- `notas`;
- `obligatorio` o `incluido`;
- `config`;
- valor comercial informativo si se requiere para contrato;
- clave estable para snapshot/materializacion.

Compatibilidad:

- mantener `ServicioPaquete` hasta migracion probada;
- el DTO de propuesta puede emitir lineas normalizadas desde `PaqueteServicio` K9 y desde `ServicioPaquete` legacy;
- conservar snapshots v1;
- nunca duplicar `ServicioEvento` al re-materializar;
- soportar masters eliminados via snapshot.

## Propuesta de evento

Flujo objetivo:

```text
Evento -> sede -> adultos -> ninos -> paquete -> incluidos -> adicionales -> cortesias -> descuento -> total
```

Ownership:

- Vistas/templates: capturan entrada y renderizan DTO.
- Service layer comercial: calcula totales y valida reglas.
- DTO/context: transporta propuesta, desglose y visibilidad.
- Modelos: persisten solo cuando se guarda propuesta/contrato.

No dispersar formulas en templates.

DTO minimo sugerido:

- evento_id;
- empresa_id;
- sede_id;
- adultos;
- ninos;
- paquete_id;
- lineas_incluidas;
- lineas_adicionales;
- lineas_cortesia;
- descuentos;
- totales;
- advertencias;
- version_calculo.

Implementado K9.4: `PropuestaEvento` guarda propuesta editable con empresa, evento, sede, adultos, ninos, paquete, descuento, estado, notas comerciales, creador/modificador y ultimo desglose calculado. Ese desglose no es snapshot contractual definitivo.

Estados K9.4/K9.5:

- `BORRADOR`;
- `PROPUESTA`;
- `EN_REVISION`;
- `ACEPTADO`;
- `CONTRATADO`;
- `CANCELADO`.

`CONTRATADO` se asigna en K9.5 solo despues de crear o recuperar idempotentemente el `ContratoEvento` v2. `ACEPTADO` por si solo no crea materializacion operativa.

## Adicionales

Un adicional puede venir de catalogo o ser manual del evento.

Modos de precio:

- `FIJO`;
- `POR_ADULTO`;
- `POR_NINO`;
- `POR_PERSONA`;
- `POR_UNIDAD`;
- `MANUAL`.

Implementado K9.4: los adicionales viven en `PropuestaLinea` con `tipo=ADICIONAL`, `servicio_catalogo` opcional, nombre manual, descripcion, modo, tarifa, cantidad, subtotal y snapshot de linea para la propuesta.

El contrato debe guardar snapshot de la tarifa usada:

- modo;
- monto unitario;
- cantidad aplicada;
- subtotal;
- nombre/categoria del servicio;
- origen catalogo/manual;
- version de calculo.

## Cortesias

K9 debe agregar conceptualmente `CORTESIA` a `ServicioEvento.modalidad`.

Una cortesia:

- pertenece al contrato;
- se muestra al cliente;
- tiene cargo cliente igual a cero;
- puede conservar valor comercial informativo;
- puede generar costo operativo;
- se materializa como `ServicioEvento`;
- no es lo mismo que incluido.

Implementado K9.4: una cortesia vive en `PropuestaLinea` con `tipo=CORTESIA`; aparece en el DTO y siempre tiene cargo cliente cero. Puede conservar valor informativo.

## Contrato de evento

Regla:

```text
CONTRATO EVENTO = PAQUETE BASE + ADICIONALES - DESCUENTOS
CORTESIAS = cargo cliente 0
```

Debe congelar:

- paquete;
- tarifa adulto;
- tarifa nino;
- adultos contratados;
- ninos contratados;
- cargo fijo;
- incluidos;
- adicionales;
- cortesias;
- descuentos;
- total final;
- sede acordada;
- duracion;
- condiciones relevantes;
- snapshots de servicios.

`ContratoEvento.snapshot_comercial` es el candidato natural para snapshot v2, pero debe convivir con `PaqueteEvento.snapshot_paquete` v1.

K9.5 implementado:

- `ContratoEvento` es la autoridad contractual K9 para propuestas aceptadas.
- `ContratoEvento.propuesta_origen` apunta a la `PropuestaEvento` de origen y es unico para evitar dos contratos del mismo acuerdo.
- `ContratoEvento.snapshot_version` identifica la version del snapshot; K9 usa `2`.
- `ContratoEvento.estado` admite `CONTRATADO` para contratos generados desde propuesta aceptada.
- `PropuestaEvento.estado` admite `CONTRATADO` y cambia a ese estado solo despues de generar el contrato.
- El servicio `generar_contrato_v2_desde_propuesta` trabaja en transaccion, bloquea la propuesta, recalcula totales server-side y persiste el snapshot congelado.
- La operacion es idempotente: si ya existe contrato para la propuesta, devuelve el contrato existente.
- El snapshot v2 guarda datos comerciales congelados: empresa, evento, sede, paquete, adultos, ninos, incluidos, adicionales, cortesias, descuentos y total final.
- El snapshot v2 no guarda costo proveedor, margen, pagos proveedor, gastos ni negociacion interna.
- K9.5 no crea `ServicioEvento`; eso queda para materializacion v2 en K9.6.
- Cambios posteriores en paquete, catalogo, propuesta o proveedor no modifican el contrato ya emitido.

Lectores implementados:

- `leer_contrato_v2` devuelve la proyeccion interna desde `ContratoEvento.snapshot_comercial`.
- `leer_contrato_publico` devuelve una proyeccion cliente sin metadata interna.
- `leer_contrato_v1_paquete_evento` adapta `PaqueteEvento.snapshot_paquete` v1 para mantener compatibilidad K8.

## ServicioEvento

`ServicioEvento` sigue siendo el nucleo operativo.

Debe representar:

- origen: `MANUAL`, `CATALOGO`, `PAQUETE`;
- modalidad: `INCLUIDO`, `ADICIONAL`, `UPGRADE`, futuro `CORTESIA`;
- prestacion: empresa, proveedor externo o por definir;
- valores comerciales congelados;
- costos operativos posteriores;
- workspace, tareas, citas, documentos, gastos y pagos relacionados.

Regla critica: cambiar proveedor o costo proveedor no modifica el contrato cliente.

## Presupuesto

No crear un segundo sistema financiero.

Separacion:

- Cliente paga contrato a empresa: `PagoClienteEvento`.
- Empresa paga proveedores/costos: `GastoEvento` + `PagoEvento`.

`ServicioEvento` puede relacionar concepto operativo con gasto o pago, pero no debe mezclar ingreso cliente con costo proveedor.

## Colaboracion

Contrato aceptado produce servicios operativos. La colaboracion sigue asi:

```text
Contrato -> ServicioEvento -> Workspace existente
```

Preservar:

- `CLIENTE_PLANNER`;
- `PLANNER_PROVEEDOR`;
- `INTERNO`;
- permisos existentes de canal.

## Invitados y RSVP

Fase posterior debe definir centralmente los estados:

- `ACTIVO`;
- `BLOQUEADO/ARCHIVADO`;
- `HISTORICO`.

Regla para invitado bloqueado:

- conserva historico;
- deja de contar como invitado activo;
- no entra en pendientes;
- no entra en mesas;
- no recibe comunicaciones;
- puede reactivarse.

La eliminacion fisica solo debe permitirse para registros sin historial relevante.

Las estadisticas de invitados deben venir de una unica service/query layer reutilizada por dashboard, filtros, exportaciones y demas modulos.

Dashboard futuro minimo:

- total activos;
- confirmados si;
- confirmados no;
- pendientes;
- bloqueados/historico.

Cada KPI debe poder actuar como filtro.

## Branding por empresa

Fase posterior controlada por DIRTEC debe permitir configurar:

- logo;
- portada/hero;
- imagen encabezado;
- color principal;
- color secundario.

El branding debe aplicarse de forma consistente a Empresa, Planner, Cliente, Proveedor y login/portal cuando corresponda.

No se permite CSS arbitrario por tenant.

## CRUD operativo y conservacion historica

El dominio operativo debe distinguir:

- `EDITAR`;
- `CANCELAR`;
- `ARCHIVAR`;
- `ELIMINAR`.

Servicios, tareas, citas, documentos y gastos con historial no deben borrarse fisicamente a ciegas.

## Auditoria transversal

Requisito futuro para contratos, servicios, paquetes, invitados y acciones operativas relevantes:

- quien modifico;
- que modifico;
- cuando;
- estado anterior/nuevo cuando aplique.

## Estados comerciales

Flujo comercial futuro:

- `BORRADOR`;
- `PROPUESTA`;
- `EN REVISION`;
- `ACEPTADO`;
- `CONTRATADO`;
- `CANCELADO`.

Una propuesta puede cambiar. Un contrato aceptado queda congelado.

## Visibilidad contractual

Mismo contrato, diferentes proyecciones:

- DIRTEC: soporte/admin segun permisos.
- Empresa: comercial completo y operativo/financiero.
- Planner: comercial y operativo del evento asignado.
- Cliente: contrato publico sin costos internos.
- Proveedor: solo su servicio operativo y documentos/canal permitidos.

Cliente no ve:

- costo proveedor;
- costo operativo;
- margen;
- notas privadas;
- pagos a proveedor;
- negociacion interna.
