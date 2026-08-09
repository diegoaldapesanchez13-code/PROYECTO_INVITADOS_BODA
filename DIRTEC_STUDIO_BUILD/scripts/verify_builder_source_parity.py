"""Valida paridad con Builder V3 y documenta deltas de tooling permitidos."""

from pathlib import Path
import hashlib

WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE.parent
SOURCE = WORKSPACE / "builder"
BASELINE = ROOT / "invitaciones" / "static" / "invitaciones" / "js" / "builder_v3"

WORKSPACE_METADATA = {
    "README.md",
    "builder.manifest.json",
    "package.json",
}

ALLOWED_TEST_DELTAS = {
    "tests/test_r3_mobile_preview.mjs",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() != ".txt":
            result[path.relative_to(root).as_posix()] = sha(path)
    return result


def main() -> None:
    source = inventory(SOURCE)
    baseline = inventory(BASELINE)

    missing = sorted(set(baseline) - set(source))
    extras = sorted(set(source) - set(baseline))
    unexpected_extras = sorted(set(extras) - WORKSPACE_METADATA)

    changed = {
        key
        for key in set(source) & set(baseline)
        if source[key] != baseline[key]
    }

    unexpected_changed = sorted(changed - ALLOWED_TEST_DELTAS)
    expected_test_deltas = sorted(changed & ALLOWED_TEST_DELTAS)

    product_files = [
        key for key in baseline
        if not key.startswith("tests/")
    ]
    product_changed = [
        key for key in product_files
        if source.get(key) != baseline.get(key)
    ]

    if missing or unexpected_extras or unexpected_changed or product_changed:
        print("PARIDAD FALLIDA")
        if missing:
            print("Faltantes:", *missing, sep="\n  - ")
        if unexpected_extras:
            print("Extras inesperados:", *unexpected_extras, sep="\n  - ")
        if unexpected_changed:
            print("Cambios inesperados:", *unexpected_changed, sep="\n  - ")
        if product_changed:
            print("Producto modificado:", *product_changed, sep="\n  - ")
        raise SystemExit(1)

    print(f"PARIDAD PRODUCTO OK: {len(product_files)} archivos de producto idénticos a V3.")
    print(
        "Tests baseline sin cambios:",
        len([key for key in baseline if key.startswith("tests/")]) - len(expected_test_deltas),
    )

    if expected_test_deltas:
        print("Delta de portabilidad permitido:")
        for item in expected_test_deltas:
            print(f"  - {item} (fileURLToPath para Windows/POSIX)")

    print(
        "Metadata propia permitida:",
        ", ".join(sorted(set(extras) & WORKSPACE_METADATA)),
    )


if __name__ == "__main__":
    main()
