/**
 * Estado local del editor que NO forma parte del Documento publicado.
 */
export class WorkspaceState {
    #value;
    #listeners = new Set();

    constructor(initial = {}) {
        this.#value = normalizeWorkspaceState(initial);
    }

    get value() {
        return clone(this.#value);
    }

    update(mutator) {
        if (typeof mutator !== "function") throw new TypeError("mutator debe ser una función.");
        const draft = this.value;
        const returned = mutator(draft);
        this.#value = normalizeWorkspaceState(
            returned && typeof returned === "object" ? returned : draft,
        );
        this.#emit();
        return this.value;
    }

    replace(value = {}) {
        this.#value = normalizeWorkspaceState(value);
        this.#emit();
        return this.value;
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        listener(this.value);
        return () => this.#listeners.delete(listener);
    }

    #emit() {
        const state = this.value;
        for (const listener of this.#listeners) listener(state);
    }
}

export function normalizeWorkspaceState(value = {}) {
    return {
        selectedCanvasId: value.selectedCanvasId ?? null,
        selectedNodeId: value.selectedNodeId ?? null,
        zoom: finiteNumber(value.zoom, 1),
        activeLeftPanel: String(value.activeLeftPanel || "assets"),
        activeInspectorTab: String(value.activeInspectorTab || "general"),
        inspectorAccordions: cloneObject(value.inspectorAccordions),
        panelScroll: cloneObject(value.panelScroll),
        previewDevice: String(value.previewDevice || "iphone-13"),
    };
}

function finiteNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function cloneObject(value) {
    return value && typeof value === "object" && !Array.isArray(value)
        ? clone(value)
        : {};
}
function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
