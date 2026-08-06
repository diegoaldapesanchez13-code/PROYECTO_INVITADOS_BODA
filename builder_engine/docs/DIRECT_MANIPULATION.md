# Direct Manipulation y Responsive Transforms

Versión de Workspace: 3

## Funciones

- mover elementos mediante pointer events;
- redimensionar desde cuatro esquinas;
- rotar desde un control superior;
- Shift ajusta la rotación a incrementos de 15 grados;
- Alt desactiva temporalmente el ajuste fino del movimiento;
- guardar una sola actualización al finalizar la operación;
- perfiles Mobile, Tablet y Desktop;
- overrides dentro de `style.responsive`.

## Contrato responsive

```json
{
  "style": {
    "x": 50,
    "y": 50,
    "width": 70,
    "responsive": {
      "mobile": {"x": 50, "width": 85},
      "tablet": {"x": 45, "width": 65},
      "desktop": {"x": 35, "width": 40}
    }
  }
}
```
