# Git release — K.8.7.8

No crear el commit estable hasta que el gate complete termine en OK en la computadora de desarrollo.

## Después del gate OK

```powershell
git status
git switch -c k8-event-platform-stable
git add .
git status
git commit -m "stable(k8.7.8): harden production baseline and deployment"
git tag -a k8.7.8-event-platform-stable-v1 -m "DIRTEC Event Studio K8.7.8 production baseline"
git push -u origin k8-event-platform-stable
git push origin k8.7.8-event-platform-stable-v1
```

Antes de `git add .` comprobar que NO entren:

```text
.env.production
.env.server
db.sqlite3
media/
backups/
staticfiles/
logs/
venv/
```

Si `db.sqlite3` o `media/` ya estuvieran versionados históricamente, no ejecutar `git rm` sin revisar primero; el baseline no debe destruir ni mover datos locales por accidente.
