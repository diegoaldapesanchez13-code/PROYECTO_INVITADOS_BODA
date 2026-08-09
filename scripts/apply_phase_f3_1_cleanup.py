"""PHASE F.3.1 — limpia archivos renombrados del runtime."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

obsolete=[
    ROOT/"DIRTEC_STUDIO_BUILD/builder/inspector/panels/section.js",
]

for path in obsolete:
    if path.exists():
        path.unlink()
        print(f"DELETE: {path.relative_to(ROOT)}")

print("PHASE F.3.1 cleanup aplicada.")
