"""Gate PHASE F.3 — Native V4 Engine."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BUILDER=ROOT/"DIRTEC_STUDIO_BUILD/builder"
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"

FORBIDDEN={
    "NODE_TYPES.SECTION",
    "sectionId",
    ".sections",
    "projectDocumentV4ToRuntime",
}

ALLOWED_LEGACY_MODULES={
    "core/schema_v4.js",
    "core/migrate.js",
}

def run(cmd,cwd=ROOT,shell=False):
    printable=cmd if isinstance(cmd,str) else " ".join(map(str,cmd))
    print(f"\n> {printable}")
    result=subprocess.run(cmd,cwd=cwd,shell=shell)
    if result.returncode:
        raise SystemExit(result.returncode)

violations=[]
for path in BUILDER.rglob("*.js"):
    rel=path.relative_to(BUILDER).as_posix()
    if rel.startswith("tests/") or rel in ALLOWED_LEGACY_MODULES:
        continue
    source=path.read_text(encoding="utf8")
    for token in FORBIDDEN:
        if token in source:
            violations.append(f"{rel}: {token}")

if violations:
    print("Runtime V3 residual detectado:")
    for item in violations:
        print(" -",item)
    raise SystemExit(1)

obsolete=BUILDER/"interaction/executors/section.js"
if obsolete.exists():
    raise SystemExit(
        "Ejecuta primero scripts/apply_phase_f3_cleanup.py "
        "para retirar section.js."
    )

run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])
run([sys.executable,ROOT/"manage.py","makemigrations","--check"])
run([
    sys.executable,ROOT/"manage.py","test",
    "invitaciones.tests_builder_django",
    "invitaciones.tests_builder_assets",
    "invitaciones.tests_builder_public",
    "invitaciones.tests_builder_v4",
])

print("\nPHASE F.3 GATE OK")
