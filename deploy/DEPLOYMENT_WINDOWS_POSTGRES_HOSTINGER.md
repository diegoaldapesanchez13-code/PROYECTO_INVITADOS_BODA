# DIRTEC Event Studio — despliegue Windows + PostgreSQL + Hostinger DNS

## Arquitectura objetivo

```text
Internet
  ↓
Dominio/subdominio (DNS administrado en Hostinger)
  ↓
IP pública del sitio donde vive el servidor
  ↓ TCP 80/443
Caddy (Windows)
  ├── /static/* → staticfiles/
  ├── /media/* → media/ solo medios públicos
  ├── bloquea prefijos privados de /media/
  └── resto → Waitress 127.0.0.1:8001
                  ↓
              Django WSGI
                  ↓
        PostgreSQL 127.0.0.1:5432
```

PostgreSQL y Django viven en la misma computadora servidor. PostgreSQL **no debe exponerse al Internet**; escuchar en localhost o firewall privado.

## Antes de mover nada

1. Cerrar K.8.7.8 y ejecutar `python scripts/verify_stable_k8_7_8.py`.
2. No borrar ni modificar `db.sqlite3` original.
3. Ejecutar `deploy/windows/backup_current_sqlite.ps1`.
4. Guardar al menos dos copias del directorio generado en `backups/`.
5. El backup contiene:
   - `db.sqlite3` original;
   - SHA256 del SQLite;
   - `data.fixture.json` portable;
   - `inventory_sqlite.json` con conteos y hashes de media;
   - copia completa de `media/`.

## Preparar la computadora servidor

Instalar:
- Python compatible con el proyecto;
- PostgreSQL;
- Git;
- Caddy;
- el código del tag estable de DIRTEC Event Studio.

Crear un venv limpio y ejecutar:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## PostgreSQL

Crear una base y un usuario **dedicados a la aplicación**. No utilizar el superusuario `postgres` como credencial de Django.

Ejemplo de nombres:

```text
DB: dirtec_event_studio
USER: dirtec_app
HOST: 127.0.0.1
PORT: 5432
```

La contraseña real se guarda solamente en `.env.production`, que está ignorado por Git.

## .env.production

Copiar `.env.example` a `.env.production` y reemplazar:

- `DJANGO_SECRET_KEY`;
- dominio real;
- `POSTGRES_PASSWORD`;
- cualquier parámetro del servidor.

Primer corte:

```text
DJANGO_DEBUG=False
DJANGO_DB_ENGINE=postgresql
SAAS_REQUIRE_SUBSCRIPTION=False
DJANGO_SECURE_HSTS_SECONDS=0
```

No activar HSTS largo hasta verificar HTTPS y dominio definitivamente.

## Migrar los datos actuales

En la computadora original:

```powershell
.\deploy\windows\backup_current_sqlite.ps1
```

Copiar el backup completo al servidor.

En el servidor, con PostgreSQL vacío:

```powershell
.\deploy\windows\import_to_postgres.ps1 -BackupDir "D:\ruta\pre_postgres_YYYYMMDD_HHMMSS"
```

El script:
1. ejecuta migraciones sobre PostgreSQL;
2. carga el fixture UTF-8;
3. reajusta secuencias PostgreSQL;
4. copia `media/`;
5. genera inventario PostgreSQL;
6. compara conteos y archivos contra el origen.

**No se cambia de producción a PostgreSQL si la comparación falla.**

## Datos que deben verificarse manualmente después de importar

- usuarios y contraseñas (probar login, no leer contraseñas);
- empresas y membresías;
- evento actual;
- datos de la boda;
- grupos de invitación y UUID;
- invitados individuales;
- RSVP;
- mesas/asignaciones;
- servicios/proveedores;
- tareas y agenda;
- conversaciones y referencias;
- documentos;
- pagos Cliente → Empresa;
- pagos Empresa → Proveedor;
- diseño Builder publicado y borrador;
- imágenes, audio y media de invitación.

## Static files

Con `.env.production` cargado:

```powershell
.\deploy\windows\prepare_release.ps1
```

Esto ejecuta checks, migraciones pendientes y `collectstatic`.

## Waitress

Django no se ejecuta con `runserver` en producción.

```powershell
.\deploy\windows\start_waitress.ps1
```

Waitress escucha únicamente en:

```text
127.0.0.1:8001
```

No abrir el puerto 8001 al router/Internet.

## Caddy y archivos privados

Copiar `deploy/windows/Caddyfile.example` y ajustar:
- dominio;
- ruta absoluta del proyecto.

Los prefijos privados quedan bloqueados en `/media/`:

```text
/media/documentos/
/media/presupuesto/
/media/colaboracion/
/media/proveedores/
/media/tareas/
```

La aplicación los entrega mediante `/secure/...` después de verificar permisos.

Los medios públicos de invitación (portadas, fondos, álbum, assets públicos) sí se sirven directamente.

## Dominio de Hostinger

La zona DNS del dominio puede permanecer administrada en Hostinger. Para apuntar un subdominio como `eventos.midominio.com`, crear el registro DNS correspondiente hacia la IP pública del servidor.

Antes de cambiar DNS verificar:
1. que la conexión tenga IP pública alcanzable;
2. que no exista CGNAT que impida recibir conexiones;
3. que el router pueda redirigir TCP 80/443 a la computadora servidor;
4. que Windows Firewall permita Caddy en 80/443;
5. que PostgreSQL/8001 **no** queden expuestos.

Si la IP pública cambia frecuentemente o existe CGNAT, no hacer un A record directo hasta elegir túnel/DDNS apropiado.

## Cutover

Cuando PostgreSQL, Caddy y Waitress estén validados localmente:

1. realizar un último backup SQLite/media;
2. detener escrituras en el servidor antiguo;
3. repetir export/import si hubo cambios desde el primer ensayo;
4. verificar inventarios;
5. arrancar Waitress y Caddy;
6. probar desde LAN usando el dominio si DNS ya resolvió;
7. probar desde una conexión externa (datos móviles);
8. cambiar DNS si todavía no se hizo;
9. monitorear `logs/django.log`.

## Backups de producción

No depender de una sola computadora. Mantener:
- backup PostgreSQL diario (`pg_dump`);
- copia diaria/incremental de `media/`;
- una copia fuera de la computadora servidor;
- prueba periódica de restauración.

## Actualizaciones futuras

Las nuevas funciones (paquetes, plantillas y capacidades Builder) se desarrollan en rama separada/offline.

Flujo recomendado:

```text
development branch
  ↓ tests
release candidate
  ↓ backup producción
migrate/collectstatic
  ↓ smoke test
stable production
```

Nunca desarrollar directamente sobre la copia que está sirviendo producción.
