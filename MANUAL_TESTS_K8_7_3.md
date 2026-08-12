# Pruebas manuales — K.8.7.3 Company Dashboard V3

1. Inicia sesión como administrador de empresa y abre el dashboard de empresa.
2. La navegación debe contener **Resumen / Eventos / Clientes / Equipo / Proveedores / Catálogos / Configuración**.
3. En Resumen revisa que los eventos, acciones de cliente/proveedor, tareas vencidas y confirmaciones correspondan solo a la empresa activa.
4. En Eventos cada tarjeta debe tener **un solo acceso operativo: Abrir evento**.
5. No debe haber accesos rápidos directos a Builder, Mesas o Calendario desde la tarjeta de empresa.
6. `Abrir evento` debe llevar al Event Dashboard V3 del evento correcto.
7. `Administrar ficha del evento` debe permitir cambiar nombre, fechas, sede, estado y Planner sin entrar a la operación del servicio.
8. Crea un evento desde Empresa y confirma que aparece en el portafolio y luego abre correctamente su Event Dashboard.
9. En Clientes confirma alta/edición/desactivación y que no se mezclen usuarios de otra empresa.
10. En Equipo confirma que solo aparecen roles internos (Admin/Ventas/Planner), no Cliente ni Proveedor.
11. En Proveedores confirma que el catálogo maestro y el acceso portal siguen funcionando.
12. En Catálogos confirma Sedes y Paquetes; no deben representar servicios ya contratados de un evento.
13. En Configuración revisa identidad, plan/capacidad y permisos del usuario actual.
14. Si el usuario no tiene permiso para catálogos, intenta una acción protegida y confirma que siga bloqueada.
15. Cambia de empresa/tenant (si eres DIRTEC) y verifica que eventos, clientes, proveedores y métricas cambien completamente.
16. Smoke test: abre un Evento, Planner Dashboard y Builder para confirmar que siguen funcionando.
