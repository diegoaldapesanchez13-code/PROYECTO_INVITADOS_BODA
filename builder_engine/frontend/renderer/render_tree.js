function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}

export function createRenderNode(input = {}) {
    if (!input || typeof input !== "object" || Array.isArray(input)) {
        throw new TypeError("createRenderNode requiere un objeto.");
    }
    const id = String(input.id || "").trim();
    const type = String(input.type || "UNKNOWN").trim().toUpperCase();
    if (!id) throw new TypeError("El nodo renderizado requiere id.");

    return Object.freeze({
        id,
        type,
        tag: String(input.tag || "div"),
        attributes: clone(input.attributes || {}),
        style: clone(input.style || {}),
        content: input.content ?? null,
        children: Object.freeze((input.children || []).map(createRenderNode)),
        source: input.source ? clone(input.source) : null,
        runtime: input.runtime ? clone(input.runtime) : null,
    });
}

export function createRenderCanvas(canvas = {}, children = []) {
    return Object.freeze({
        id: String(canvas.id || ""),
        name: String(canvas.name || "Lienzo"),
        order: Number.isFinite(Number(canvas.order)) ? Number(canvas.order) : 0,
        width: Number(canvas.width || 390),
        height: Number(canvas.height || 844),
        style: clone(canvas.style || {}),
        children: Object.freeze(children.map(createRenderNode)),
    });
}

export function createRenderResult({ mode, document, canvases, metadata = {} }) {
    return Object.freeze({
        mode,
        documentVersion: Number(document?.documentVersion || 1),
        schemaVersion: Number(document?.schemaVersion || 1),
        canvases: Object.freeze(canvases || []),
        metadata: Object.freeze(clone(metadata)),
    });
}
