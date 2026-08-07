# FASE 6.8 - Inspector Universal Base

## Objetivo

Crear una primera base de inspector unico para evitar que el editor dependa de paneles separados para cada tipo de elemento.

## Elementos soportados

- `section`: seccion completa.
- `layer`: capa activa de la seccion.
- `real`: contenido real de secciones dinamicas.
- `component`: componente persistente.

## Controles comunes

- X
- Y
- ancho
- alto / escala
- rotacion
- opacidad
- z-index
- bloquear
- ocultar

## Compatibilidad

El inspector no elimina los paneles actuales. Convive con:

- propiedades de seccion,
- contenido real,
- propiedades de componentes,
- panel de contenido rapido,
- administrador de assets.

Esto permite migrar el editor poco a poco sin romper el flujo actual.

## Siguiente paso recomendado

Crear el `Component Tree`:

```text
Pagina
  Seccion
    Capa
    Contenido real
    Componente
```

El inspector debe leer la seleccion desde ese arbol y no solamente desde clicks en el canvas.
