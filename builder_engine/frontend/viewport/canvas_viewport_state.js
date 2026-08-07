export const VIEWPORT_MODES = Object.freeze({
    EDIT: "EDIT",
    PREVIEW_CONTINUOUS: "PREVIEW_CONTINUOUS",
});

export class CanvasViewportState {
    #state;

    constructor(initial = {}) {
        this.#state = normalize(initial);
    }

    get value() {
        return clone(this.#state);
    }

    setMode(mode) {
        this.#state.mode = Object.values(VIEWPORT_MODES).includes(mode)
            ? mode
            : VIEWPORT_MODES.EDIT;
        return this.value;
    }

    setZoom(zoom) {
        this.#state.zoom = clamp(zoom, 0.25, 3, 1);
        return this.value;
    }

    setDevice(device) {
        this.#state.device = ["mobile", "tablet", "desktop"].includes(device)
            ? device
            : "mobile";
        return this.value;
    }

    setActiveCanvas(canvasId) {
        this.#state.activeCanvasId = canvasId ?? null;
        return this.value;
    }
}

function normalize(value = {}) {
    return {
        mode: Object.values(VIEWPORT_MODES).includes(value.mode)
            ? value.mode
            : VIEWPORT_MODES.EDIT,
        zoom: clamp(value.zoom, 0.25, 3, 1),
        device: ["mobile", "tablet", "desktop"].includes(value.device)
            ? value.device
            : "mobile",
        activeCanvasId: value.activeCanvasId ?? null,
        showRulers: value.showRulers !== false,
        showGrid: Boolean(value.showGrid),
    };
}

function clamp(value, min, max, fallback) {
    const parsed = Number(value);
    const safe = Number.isFinite(parsed) ? parsed : fallback;
    return Math.min(Math.max(safe, min), max);
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
