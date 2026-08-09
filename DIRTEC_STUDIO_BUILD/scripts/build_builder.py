from pathlib import Path
import shutil

WORKSPACE = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WORKSPACE.parent
SOURCE = WORKSPACE / "builder"
DESTINATION = PROJECT_ROOT / "invitaciones" / "static" / "invitaciones" / "builder"
RUNTIME_EXTENSIONS = {".js", ".css", ".json"}
EXCLUDED_NAMES = {"package.json", "builder.manifest.json"}

def is_runtime(path):
    rel = path.relative_to(SOURCE)
    return (
        path.is_file()
        and "tests" not in rel.parts
        and path.suffix.lower() in RUNTIME_EXTENSIONS
        and path.name not in EXCLUDED_NAMES
    )

def main():
    if not SOURCE.exists():
        raise SystemExit(f"No existe: {SOURCE}")
    if DESTINATION.exists():
        shutil.rmtree(DESTINATION)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    files = [p for p in SOURCE.rglob("*") if is_runtime(p)]
    for src in files:
        dst = DESTINATION / src.relative_to(SOURCE)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"DIRTEC Studio Builder compilado: {len(files)} archivos")
    print(f"Fuente: {SOURCE}")
    print(f"Destino: {DESTINATION}")

if __name__ == "__main__":
    main()
