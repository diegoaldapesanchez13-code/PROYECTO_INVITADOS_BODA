"""Hotfix 11.4.1: compatibilidad del resultado de LayerStackService."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = (
    ROOT
    / "builder_engine"
    / "frontend"
    / "layers"
    / "layer_stack_service.js"
)

OLD = """function result(nodes, metadata) {
    return Object.freeze({
        nodes,
        transaction: Object.freeze({
            ...metadata,
            timestamp: Date.now(),
        }),
    });
}"""

NEW = r"""/**
 * Resultado compatible del LayerStack.
 *
 * Se retorna el propio arreglo para conservar el contrato histórico:
 * `result.map(...)`, `result.length`, `result[index]`.
 *
 * El mismo arreglo expone además:
 * `result.nodes` y `result.transaction`.
 */
function result(nodes, metadata) {
    const transaction = Object.freeze({
        ...metadata,
        timestamp: Date.now(),
    });

    Object.defineProperties(nodes, {
        nodes: {
            value: nodes,
            enumerable: false,
            configurable: false,
            writable: false,
        },
        transaction: {
            value: transaction,
            enumerable: false,
            configurable: false,
            writable: false,
        },
    });

    return nodes;
}"""


def apply():
    text = TARGET.read_text(encoding="utf-8")

    if "Se retorna el propio arreglo para conservar" in text:
        print("Hotfix 11.4.1 ya estaba aplicado.")
        return

    if OLD not in text:
        raise SystemExit(
            "No se encontró la función result() esperada. "
            "Revisa la versión de layer_stack_service.js."
        )

    TARGET.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("Hotfix 11.4.1 aplicado correctamente.")


if __name__ == "__main__":
    apply()
