import { createCanvas, normalizeCanvasCollection } from "../canvas_schema.js";

/**
 * Traduce las SECTION del Builder R3 al contrato de Canvas del Engine.
 * Permite migración incremental sin modificar todavía el editor activo.
 */
export function canvasesFromR3Document(r3Document = {}) {
    const sections = Array.isArray(r3Document.sections) ? r3Document.sections : [];
    return normalizeCanvasCollection(sections.map((section, index) => createCanvas({
        id: section.id,
        name: section.name || `Lienzo ${index + 1}`,
        order: section.order ?? index,
        width: normalizeR3Width(section.width),
        height: section.height ?? section.minHeight,
        minHeight: section.minHeight,
        maxHeight: section.maxHeight,
        visible: section.visible,
        locked: section.locked,
        style: section.style,
        nodes: Array.isArray(section.children) ? section.children : [],
        metadata: {
            source: "builder-r3",
            sourceType: section.type || "SECTION",
            coordinateSpace: section.coordinateSpace || "DOCUMENT",
        },
    })));
}

export function applyCanvasesToR3Document(r3Document = {}, canvases = []) {
    const source = clone(r3Document || {});
    source.sections = normalizeCanvasCollection(canvases).map((canvas) => ({
        id: canvas.id,
        type: "SECTION",
        name: canvas.name,
        order: canvas.order,
        width: 100,
        height: canvas.height,
        minHeight: canvas.minHeight,
        maxHeight: canvas.maxHeight,
        visible: canvas.visible,
        locked: canvas.locked,
        style: clone(canvas.style),
        children: clone(canvas.nodes),
        coordinateSpace: canvas.metadata?.coordinateSpace || "DOCUMENT",
    }));
    return source;
}

function normalizeR3Width(value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed) || parsed <= 0 || parsed === 100) return 390;
    return parsed;
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
