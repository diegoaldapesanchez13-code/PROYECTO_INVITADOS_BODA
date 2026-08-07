/**
 * Registro desacoplado de servicios y extensiones del Builder.
 * El Kernel conoce contratos, no implementaciones concretas.
 */
export class BuilderRegistry {
    #entries = new Map();

    register(name, implementation, options = {}) {
        const key = normalizeKey(name);
        if (!implementation) {
            throw new TypeError(`La implementación de "${key}" es obligatoria.`);
        }
        if (this.#entries.has(key) && options.replace !== true) {
            throw new Error(`El módulo "${key}" ya está registrado.`);
        }
        this.#entries.set(key, implementation);
        return implementation;
    }

    unregister(name) {
        return this.#entries.delete(normalizeKey(name));
    }

    has(name) {
        return this.#entries.has(normalizeKey(name));
    }

    get(name, options = {}) {
        const key = normalizeKey(name);
        const implementation = this.#entries.get(key);
        if (!implementation && options.required !== false) {
            throw new Error(`El módulo "${key}" no está registrado.`);
        }
        return implementation ?? null;
    }

    list() {
        return [...this.#entries.keys()];
    }

    clear() {
        this.#entries.clear();
    }
}

function normalizeKey(value) {
    const key = String(value || "").trim().toLowerCase();
    if (!key) throw new TypeError("El nombre del módulo es obligatorio.");
    return key;
}
