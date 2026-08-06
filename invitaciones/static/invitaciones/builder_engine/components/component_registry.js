import {
    normalizeComponentDefinition,
    validateComponentDefinition,
} from "./component_contract.js";

export class ComponentRegistry {
    #definitions = new Map();

    register(raw, options = {}) {
        const result = validateComponentDefinition(raw);
        if (!result.valid) throw new TypeError(result.errors.join("\n"));
        const definition = normalizeComponentDefinition(raw);
        if (this.#definitions.has(definition.type) && options.replace !== true) {
            throw new Error(`El componente "${definition.type}" ya está registrado.`);
        }
        this.#definitions.set(definition.type, definition);
        return this.get(definition.type);
    }

    registerMany(definitions = [], options = {}) {
        return definitions.map((definition) => this.register(definition, options));
    }

    unregister(type) {
        return this.#definitions.delete(normalizeType(type));
    }

    has(type) {
        return this.#definitions.has(normalizeType(type));
    }

    get(type, options = {}) {
        const definition = this.#definitions.get(normalizeType(type));
        if (!definition && options.required !== false) {
            throw new Error(`Componente no registrado: ${type}`);
        }
        return definition ? clone(definition) : null;
    }

    list(options = {}) {
        return [...this.#definitions.values()]
            .filter((definition) => options.includeLegacy !== false || !definition.legacy)
            .filter((definition) => !options.category || definition.category === options.category)
            .map(clone);
    }

    supports(type, capability) {
        const definition = this.#definitions.get(normalizeType(type));
        return Boolean(definition?.capabilities.includes(String(capability)));
    }

    clear() {
        this.#definitions.clear();
    }
}

function normalizeType(value) {
    return String(value || "").trim().toUpperCase();
}
function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
