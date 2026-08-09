from pathlib import Path
import hashlib

WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE.parent
SOURCE = WORKSPACE / "builder"
DEST = ROOT / "invitaciones" / "static" / "invitaciones" / "builder"
EXT={".js",".css",".json"}
EXCLUDED={"package.json","builder.manifest.json"}

def runtime(p):
    rel=p.relative_to(SOURCE)
    return p.is_file() and "tests" not in rel.parts and p.suffix.lower() in EXT and p.name not in EXCLUDED

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    expected={p.relative_to(SOURCE).as_posix():sha(p) for p in SOURCE.rglob("*") if runtime(p)}
    actual={p.relative_to(DEST).as_posix():sha(p) for p in DEST.rglob("*") if p.is_file()} if DEST.exists() else {}
    missing=sorted(set(expected)-set(actual)); extra=sorted(set(actual)-set(expected))
    changed=sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])
    if missing or extra or changed:
        print("BUILD INVALIDO", {"missing":missing,"extra":extra,"changed":changed})
        raise SystemExit(1)
    print(f"BUILD OK: {len(actual)} archivos coinciden exactamente con la fuente runtime.")

if __name__ == "__main__":
    main()
