export class BlueprintRegistry {
    #blueprints = new Map();

    register(raw, options = {}) {
        const blueprint = normalizeBlueprint(raw);
        if (this.#blueprints.has(blueprint.id) && options.replace !== true) {
            throw new Error(`El blueprint "${blueprint.id}" ya está registrado.`);
        }
        this.#blueprints.set(blueprint.id, blueprint);
        return this.get(blueprint.id);
    }

    get(id, options = {}) {
        const blueprint = this.#blueprints.get(normalizeId(id));
        if (!blueprint && options.required !== false) {
            throw new Error(`Blueprint no registrado: ${id}`);
        }
        return blueprint ? clone(blueprint) : null;
    }

    list() {
        return [...this.#blueprints.values()].map(clone);
    }

    create(id, context = {}) {
        const blueprint = this.#blueprints.get(normalizeId(id));
        if (!blueprint) throw new Error(`Blueprint no registrado: ${id}`);
        return blueprint.create(clone(context));
    }
}

function normalizeBlueprint(raw = {}) {
    const id = normalizeId(raw.id);
    if (typeof raw.create !== "function") {
        throw new TypeError(`El blueprint "${id}" requiere create().`);
    }
    return Object.freeze({
        id,
        version: String(raw.version || "1.0.0"),
        label: String(raw.label || id),
        rootType: String(raw.rootType || "CONTAINER").toUpperCase(),
        create: raw.create,
    });
}
function normalizeId(value) {
    const id = String(value || "").trim().toLowerCase();
    if (!id) throw new TypeError("El ID del blueprint es obligatorio.");
    return id;
}
function clone(value) {
    if (typeof structuredClone === "function") {
        try { return structuredClone(value); } catch {}
    }
    if (Array.isArray(value)) return value.map(clone);
    if (value && typeof value === "object") {
        return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, clone(v)]));
    }
    return value;
}
