"""Gate PHASE F.3.1 — Browser import graph."""
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
BUILDER=ROOT/"DIRTEC_STUDIO_BUILD/builder"
WORKSPACE=ROOT/"DIRTEC_STUDIO_BUILD"

IMPORT_RE=re.compile(
    r"(?:from\\s+[\"']([^\"']+)[\"']|import\\(\\s*[\"']([^\"']+)[\"']\\s*\\))"
)

missing=[]

for path in BUILDER.rglob("*.js"):
    source=path.read_text(encoding="utf8")
    for match in IMPORT_RE.finditer(source):
        target=match.group(1) or match.group(2)
        if not target.startswith("."):
            continue
        resolved=(path.parent/target).resolve()
        if not resolved.exists():
            missing.append(
                (
                    path.relative_to(BUILDER).as_posix(),
                    target,
                )
            )

if missing:
    print("Imports relativos rotos:")
    for source,target in missing:
        print(f" - {source} -> {target}")
    raise SystemExit(1)

def run(cmd,cwd=ROOT,shell=False):
    printable=cmd if isinstance(cmd,str) else " ".join(map(str,cmd))
    print(f"\\n> {printable}")
    result=subprocess.run(cmd,cwd=cwd,shell=shell)
    if result.returncode:
        raise SystemExit(result.returncode)

run("node --test builder/tests/*.mjs",cwd=WORKSPACE,shell=True)
run([sys.executable,WORKSPACE/"scripts/build_builder.py"])
run([sys.executable,WORKSPACE/"scripts/verify_builder_build.py"])
run([sys.executable,ROOT/"manage.py","check"])

print("\\nPHASE F.3.1 GATE OK")
