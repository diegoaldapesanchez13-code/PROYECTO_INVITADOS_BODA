import { BuilderRegistry } from "../app/registry.js";
import {
    normalizeComponentDefinition,
    validateComponentDefinition,
} from "../components/component_contract.js";

/** API interna de extensiones del DIRTEC Builder Engine. */
export class BuilderSDK {
    #registry;

    constructor(registry = new BuilderRegistry()) {
        this.#registry = registry;
    }

    get registry() { return this.#registry; }

    registerComponent(name, component) {
        const raw = { ...component, type: component?.type || name };
        const result = validateComponentDefinition(raw);
        if (!result.valid) throw new TypeError(result.errors.join("\n"));
        const normalized = normalizeComponentDefinition(raw);
        return this.#registry.register(`component:${normalized.type}`, normalized);
    }

    registerTheme(name, theme) { return this.#registry.register(`theme:${name}`, theme); }
    registerInspector(name, inspector) { return this.#registry.register(`inspector:${name}`, inspector); }
    registerRenderer(name, renderer) { return this.#registry.register(`renderer:${name}`, renderer); }
    registerInteraction(name, interaction) { return this.#registry.register(`interaction:${name}`, interaction); }

    registerBlueprint(name, blueprint) {
        if (typeof blueprint?.create !== "function") {
            throw new TypeError(`El blueprint "${name}" requiere create().`);
        }
        return this.#registry.register(`blueprint:${name}`, blueprint);
    }
}
