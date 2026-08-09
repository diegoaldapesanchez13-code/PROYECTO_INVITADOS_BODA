# Gates obligatorios para PHASE E.2

E.2 no se considera terminada por "eliminar archivos".

Debe demostrar:

1. `python manage.py check` → PASS.
2. `makemigrations --check` → sin migraciones accidentales.
3. Builder tests → PASS.
4. Builder Django tests → PASS.
5. Asset tests → PASS.
6. Public Renderer tests → PASS.
7. Dashboard tests afectados → PASS.
8. búsqueda de rutas legacy → cero runtime.
9. búsqueda de `editor_invitacion.html` → cero referencias.
10. búsqueda de `ver_invitacion.html` → cero referencias.
11. búsqueda de `builder_v3` → solo documentación histórica permitida.
12. invitación publicada real → abre.
13. evento sin publicación → respuesta controlada, no legacy.
14. RSVP → GET/POST.
15. Assets imagen/video → siguen funcionando.

## Regla de rollback

El tag estable y Git conservan todo el código eliminado.

No se crearán carpetas `legacy/`, `.bak`, `old/` ni copias paralelas dentro del
repositorio.
