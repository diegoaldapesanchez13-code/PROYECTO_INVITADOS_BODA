export class RendererRegistry {
    #renderers = new Map();
    #fallback = null;

    register(type, renderer, options = {}) {
        const key = normalizeType(type);
        if (typeof renderer !== "function" && typeof renderer?.render !== "function") {
            throw new TypeError(`Renderer para ${key} debe ser función u objeto con render().`);
        }
        if (this.#renderers.has(key) && options.replace !== true) {
            throw new Error(`Ya existe renderer para ${key}.`);
        }
        this.#renderers.set(key, renderer);
        return renderer;
    }

    registerFallback(renderer) {
        if (typeof renderer !== "function" && typeof renderer?.render !== "function") {
            throw new TypeError("Fallback renderer inválido.");
        }
        this.#fallback = renderer;
        return renderer;
    }

    unregister(type) { return this.#renderers.delete(normalizeType(type)); }
    has(type) { return this.#renderers.has(normalizeType(type)); }

    resolve(type, options = {}) {
        const renderer = this.#renderers.get(normalizeType(type)) || this.#fallback;
        if (!renderer && options.required !== false) {
            throw new Error(`No existe renderer para ${type}.`);
        }
        return renderer || null;
    }

    list() { return [...this.#renderers.keys()]; }
}

function normalizeType(value) {
    const type = String(value || "").trim().toUpperCase();
    if (!type) throw new TypeError("El tipo de nodo es obligatorio.");
    return type;
}
