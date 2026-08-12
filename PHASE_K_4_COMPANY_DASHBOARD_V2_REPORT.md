# PHASE K.4 — COMPANY DASHBOARD V2

## Scope
K.4 reorganiza el dashboard del administrador de empresa como home operativo SaaS de un solo tenant.

## Decisiones de producto
- El dashboard de empresa no presenta selector de empresa.
- El tenant autenticado se muestra como contexto bloqueado en el sidebar.
- DIRTEC sigue siendo la unica capa con administracion cross-company.
- Inicio pasa a ser ejecutivo: eventos activos, clientes, planners y pendientes criticos.
- Eventos se promueve como centro del trabajo diario.
- Uso del plan se conserva, pero pasa a una franja compacta secundaria.
- Se conservan los formularios y acciones existentes de crear/editar/desactivar/eliminar.
- Se conservan Clientes, Equipo, Catalogos/Proveedores y Operacion.
- Sin cambios de modelos ni migraciones.

## UX
- Sidebar mas compacto y jerarquico.
- Header de empresa simplificado.
- KPIs ejecutivos.
- Lista de eventos recientes con acceso directo.
- Panel de prioridades: eventos sin planner, RSVP, tareas vencidas y pagos vencidos.
- Responsive desktop/tablet/mobile.
- Formularios de gestion usan ancho completo para evitar paneles comprimidos.

## Protecciones
- K.3 Identity/Login no se modifica.
- Tenant authorization no se modifica.
- Django admin sigue reservado a DIRTEC.
- Builder, RSVP, persistence, schema, Experience y runtime publico no se modifican.

## Archivos completos para reemplazo
- invitaciones/templates/invitaciones/dashboard_empresa.html
- invitaciones/static/invitaciones/css/role_dashboards.css

## Verificacion
La validacion Django no pudo ejecutarse en el runtime de empaquetado porque ese entorno no tiene Django instalado. K.4 solo modifica template/CSS y no toca Python. Ejecutar localmente:

python manage.py check
python manage.py test core.tests_identity_k3 invitaciones.tests_role_redirect_k3 invitaciones.tests_identity_forms_k3

## Acceptance manual
1. Login ADMIN_EMPRESA.
2. Confirmar que no existe selector de empresa.
3. Confirmar empresa activa bloqueada en sidebar.
4. Abrir Inicio/Eventos/Clientes/Equipo/Catalogos/Operacion.
5. Crear/editar evento de prueba.
6. Abrir Builder desde evento.
7. Crear/editar cliente y planner.
8. Revisar proveedor y credenciales de portal.
9. Revisar responsive sin solapamientos.
