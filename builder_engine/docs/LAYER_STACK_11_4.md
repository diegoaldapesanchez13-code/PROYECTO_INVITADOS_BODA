# Sprint 11.4 — Layer Stack Core

## Fuente canónica

```text
parent.children[]
```

El arreglo se interpreta de atrás hacia delante:

```text
children[0]       = fondo
children[last]    = frente
```

`style.zIndex` es un valor derivado y normalizado:

```text
index + 1
```

## Operaciones

- subir una capa;
- bajar una capa;
- traer al frente;
- enviar al fondo;
- mover antes;
- mover después;
- mover dentro de Card/Container/Group;
- bloquear;
- ocultar;
- renombrar;
- duplicar;
- eliminar.

## Reglas

- Las operaciones relativas solo comparan hermanos.
- No existe z-index responsive.
- Mover dentro de un contenedor cambia el padre real.
- No se permiten ciclos.
- Las capas bloqueadas no se reordenan.
- Todas las ramas se normalizan después de cada mutación.
- El servicio devuelve metadatos de transacción para History.

## Árbol visual

`LayerTreeState` conserva:

- selección;
- expand/collapse;
- drag actual;
- target;
- placement.

## Próximo paso

Sprint 11.4.1 conectará este servicio a un Layer Lab visual aislado con Universal Renderer y Transform Lab.
