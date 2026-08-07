import {
    CANVAS_OVERFLOW,
    CANVAS_SIZING,
    DEFAULT_CANVAS_HEIGHT,
    MAX_CANVAS_HEIGHT,
    MIN_CANVAS_HEIGHT,
    MOBILE_CANVAS_WIDTH,
} from "./constants.js";

export function createCanvas(overrides = {}) {
    const id = String(overrides.id || createId());
    return normalizeCanvas({
        id,
        name: overrides.name || "Nuevo lienzo",
        order: overrides.order ?? 0,
        width: overrides.width ?? MOBILE_CANVAS_WIDTH,
        height: overrides.height ?? DEFAULT_CANVAS_HEIGHT,
        minHeight: overrides.minHeight ?? 0,
        maxHeight: overrides.maxHeight ?? 0,
        visible: overrides.visible !== false,
        locked: overrides.locked === true,
        style: overrides.style || {},
        nodes: overrides.nodes || [],
        metadata: overrides.metadata || {},
    });
}

export function normalizeCanvas(raw = {}) {
    const style = isObject(raw.style) ? raw.style : {};
    return {
        id: String(raw.id || createId()),
        name: String(raw.name || "Nuevo lienzo"),
        order: nonNegativeInteger(raw.order, 0),
        width: clampNumber(raw.width, 1, 10000, MOBILE_CANVAS_WIDTH),
        height: normalizeHeight(raw.height),
        minHeight: clampNumber(raw.minHeight, 0, MAX_CANVAS_HEIGHT, 0),
        maxHeight: clampNumber(raw.maxHeight, 0, MAX_CANVAS_HEIGHT, 0),
        visible: raw.visible !== false,
        locked: raw.locked === true,
        style: {
            paddingX: clampNumber(style.paddingX, 0, 1000, 0),
            paddingY: clampNumber(style.paddingY, 0, 1000, 0),
            overflow: Object.values(CANVAS_OVERFLOW).includes(style.overflow)
                ? style.overflow
                : CANVAS_OVERFLOW.HIDDEN,
            direction: style.direction === "row" ? "row" : "column",
            align: normalizeChoice(style.align, ["start", "center", "end", "stretch"], "stretch"),
            justify: normalizeChoice(style.justify, ["start", "center", "end", "space-between"], "start"),
            gap: clampNumber(style.gap, 0, 1000, 0),
            sizingX: normalizeChoice(style.sizingX, Object.values(CANVAS_SIZING), CANVAS_SIZING.FIXED),
            sizingY: normalizeChoice(style.sizingY, Object.values(CANVAS_SIZING), CANVAS_SIZING.FIXED),
        },
        nodes: Array.isArray(raw.nodes) ? clone(raw.nodes) : [],
        metadata: isObject(raw.metadata) ? clone(raw.metadata) : {},
    };
}

export function normalizeCanvasCollection(raw = []) {
    const canvases = Array.isArray(raw) ? raw.map(normalizeCanvas) : [];
    return canvases
        .sort((a, b) => a.order - b.order)
        .map((canvas, index) => ({ ...canvas, order: index }));
}

export function validateCanvas(canvas) {
    const errors = [];
    if (!isObject(canvas)) return { valid: false, errors: ["El lienzo debe ser un objeto."] };
    if (!String(canvas.id || "").trim()) errors.push("El lienzo requiere id.");
    if (!String(canvas.name || "").trim()) errors.push("El lienzo requiere nombre.");
    if (!Number.isFinite(Number(canvas.width)) || Number(canvas.width) <= 0) errors.push("width debe ser positivo.");
    if (canvas.height !== "auto" && (!Number.isFinite(Number(canvas.height)) || Number(canvas.height) < MIN_CANVAS_HEIGHT)) {
        errors.push(`height debe ser "auto" o al menos ${MIN_CANVAS_HEIGHT}.`);
    }
    if (!Array.isArray(canvas.nodes)) errors.push("nodes debe ser un arreglo.");
    return { valid: errors.length === 0, errors };
}

function normalizeHeight(value) {
    if (value === "auto") return "auto";
    return clampNumber(value, MIN_CANVAS_HEIGHT, MAX_CANVAS_HEIGHT, DEFAULT_CANVAS_HEIGHT);
}

function normalizeChoice(value, allowed, fallback) {
    return allowed.includes(value) ? value : fallback;
}

function nonNegativeInteger(value, fallback) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed >= 0 ? parsed : fallback;
}

function clampNumber(value, min, max, fallback) {
    const parsed = Number(value);
    const safe = Number.isFinite(parsed) ? parsed : fallback;
    return Math.min(Math.max(safe, min), max);
}

function createId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `canvas-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
