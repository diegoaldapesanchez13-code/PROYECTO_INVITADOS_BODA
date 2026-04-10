# PROYECTO_INVITADOS_BODA

Dashboard para gestión de invitados e invitaciones personales y familiares.

## Descripción

Este es un proyecto Django para gestionar invitaciones de boda y eventos relacionados.

- Aplicación principal: `invitaciones`
- Base de datos: SQLite (`db.sqlite3`)
- Vista de invitaciones, panel de control y recursos estáticos

## Requisitos

- Python 3.11+ (o similar)
- Django instalado
- Dependencias en `requirements.txt`

## Instalación

1. Crear y activar el entorno virtual:

```bash
python -m venv venv
venv\Scripts\Activate.ps1  # Windows PowerShell
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar migraciones:

```bash
python manage.py migrate
```

4. Iniciar el servidor de desarrollo:

```bash
python manage.py runserver
```

## Estructura del proyecto

- `manage.py`: comando de administración de Django
- `config/`: configuración del proyecto
- `invitaciones/`: aplicación principal del proyecto
- `templates/`: plantillas HTML
- `static/`: recursos estáticos

## Versionado

Este proyecto está versionado con Git y ya está preparado para GitHub.

## Publicar en GitHub

```bash
git remote set-url origin https://github.com/diegoaldapesanchez13-code/PROYECTO_INVITADOS_BODA.git
git push -u origin main
```
