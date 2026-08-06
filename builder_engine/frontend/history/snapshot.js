function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}

export function createSnapshot(document, meta = {}) {
    return Object.freeze({
        id: meta.id || cryptoSafeId(),
        label: String(meta.label || "Cambio"),
        mergeKey: meta.mergeKey ? String(meta.mergeKey) : null,
        createdAt: Number(meta.createdAt || Date.now()),
        document: clone(document),
    });
}

export function restoreSnapshot(snapshot) {
    if (!snapshot?.document) throw new TypeError("Snapshot inválido.");
    return clone(snapshot.document);
}

function cryptoSafeId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `history-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
