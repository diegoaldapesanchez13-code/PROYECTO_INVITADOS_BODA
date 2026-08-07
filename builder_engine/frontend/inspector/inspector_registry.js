import { INSPECTOR_PANEL_KINDS } from "./constants.js";

export class InspectorRegistry {
    #panels = new Map();

    register(panel, options = {}) {
        const normalized = normalizePanel(panel);
        if (this.#panels.has(normalized.id) && options.replace !== true) {
            throw new Error(`El panel de Inspector "${normalized.id}" ya está registrado.`);
        }
        this.#panels.set(normalized.id, normalized);
        return normalized;
    }

    unregister(id) {
        return this.#panels.delete(String(id || "").trim());
    }

    get(id) {
        return this.#panels.get(String(id || "").trim()) || null;
    }

    list(context = {}) {
        return [...this.#panels.values()]
            .filter((panel) => matchesPanel(panel, context))
            .sort((a, b) => a.order - b.order || a.id.localeCompare(b.id));
    }

    clear() {
        this.#panels.clear();
    }
}

export function normalizePanel(panel = {}) {
    const id = String(panel.id || "").trim();
    if (!id) throw new TypeError("El panel de Inspector requiere id.");
    const kind = INSPECTOR_PANEL_KINDS.includes(panel.kind) ? panel.kind : "group";
    return Object.freeze({
        id,
        kind,
        title: String(panel.title || id),
        order: Number.isFinite(Number(panel.order)) ? Number(panel.order) : 100,
        types: normalizeList(panel.types),
        capabilities: normalizeList(panel.capabilities),
        tab: String(panel.tab || "properties"),
        controls: Array.isArray(panel.controls) ? [...panel.controls] : [],
        visible: typeof panel.visible === "function" ? panel.visible : null,
        metadata: panel.metadata && typeof panel.metadata === "object" ? { ...panel.metadata } : {},
    });
}

function matchesPanel(panel, context) {
    const node = context.node || {};
    if (panel.tab && context.tab && panel.tab !== context.tab) return false;
    if (panel.types.length && !panel.types.includes(String(node.type || "").toUpperCase())) return false;
    if (panel.capabilities.length) {
        const nodeCapabilities = new Set((node.capabilities || []).map(String));
        if (!panel.capabilities.every((capability) => nodeCapabilities.has(capability))) return false;
    }
    return panel.visible ? panel.visible(context) !== false : true;
}

function normalizeList(value) {
    return Array.isArray(value)
        ? value.map((item) => String(item).toUpperCase()).filter(Boolean)
        : [];
}
