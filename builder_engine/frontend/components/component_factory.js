export class ComponentFactory {
    #registry;
    #idFactory;

    constructor(registry, options = {}) {
        if (!registry?.get) throw new TypeError("ComponentFactory requiere ComponentRegistry.");
        this.#registry = registry;
        this.#idFactory = options.idFactory || defaultIdFactory;
    }

    create(type, overrides = {}, context = {}) {
        const definition = this.#registry.get(type);
        const base = clone(definition.defaults);
        const custom = definition.factory
            ? definition.factory({ definition, overrides: clone(overrides), context: clone(context) })
            : {};

        const node = deepMerge({
            id: overrides.id || this.#idFactory(definition.type),
            type: definition.type,
            name: definition.label,
            visible: true,
            locked: false,
            content: {},
            style: {},
            children: [],
        }, base, custom, overrides);

        node.type = definition.type;
        node.id = String(node.id || this.#idFactory(definition.type));
        node.children = Array.isArray(node.children) ? node.children : [];

        const errors = definition.validate?.(clone(node), context) || [];
        if (Array.isArray(errors) && errors.length) {
            throw new Error(errors.join("\n"));
        }
        return node;
    }
}

function defaultIdFactory(type) {
    const suffix = globalThis.crypto?.randomUUID
        ? globalThis.crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    return `${String(type).toLowerCase()}-${suffix}`;
}
function deepMerge(...values) {
    const output = {};
    for (const value of values) mergeInto(output, value);
    return output;
}
function mergeInto(target, source) {
    if (!source || typeof source !== "object" || Array.isArray(source)) return target;
    for (const [key, value] of Object.entries(source)) {
        if (value && typeof value === "object" && !Array.isArray(value)) {
            target[key] = mergeInto(
                target[key] && typeof target[key] === "object" && !Array.isArray(target[key])
                    ? target[key]
                    : {},
                value,
            );
        } else {
            target[key] = clone(value);
        }
    }
    return target;
}
function clone(value) {
    if (value === undefined) return undefined;
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
