export class InteractionRegistry {
    #executors = new Map();

    register(type, executor, options = {}) {
        const key = normalizeType(type);
        if (!executor || typeof executor.execute !== "function") {
            throw new TypeError(`El ejecutor "${key}" requiere execute().`);
        }
        if (this.#executors.has(key) && options.replace !== true) {
            throw new Error(`El ejecutor "${key}" ya está registrado.`);
        }
        this.#executors.set(key, executor);
        return executor;
    }

    get(type, options = {}) {
        const key = normalizeType(type);
        const executor = this.#executors.get(key);
        if (!executor && options.required !== false) {
            throw new Error(`Ejecutor no registrado: ${key}`);
        }
        return executor ?? null;
    }

    has(type) {
        return this.#executors.has(normalizeType(type));
    }

    list() {
        return [...this.#executors.keys()];
    }
}

function normalizeType(value) {
    const type = String(value || "").trim().toUpperCase();
    if (!type) throw new TypeError("El tipo de interacción es obligatorio.");
    return type;
}
