"""PHASE F.3 cleanup — remove obsolete V3 runtime files."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

DELETE=[
    ROOT/"DIRTEC_STUDIO_BUILD/builder/interaction/executors/section.js",
]

for path in DELETE:
    if path.exists():
        path.unlink()
        print(f"DELETE: {path.relative_to(ROOT)}")

print("PHASE F.3 cleanup aplicada.")
