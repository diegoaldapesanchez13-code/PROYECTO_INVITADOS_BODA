import { BuilderRegistry } from "../app/registry.js";

/** API mínima de extensiones. Se ampliará al migrar cada módulo completo. */
export class BuilderSDK {
    #registry;

    constructor(registry = new BuilderRegistry()) {
        this.#registry = registry;
    }

    get registry() { return this.#registry; }
    registerComponent(name, component) { return this.#registry.register(`component:${name}`, component); }
    registerTheme(name, theme) { return this.#registry.register(`theme:${name}`, theme); }
    registerInspector(name, inspector) { return this.#registry.register(`inspector:${name}`, inspector); }
    registerRenderer(name, renderer) { return this.#registry.register(`renderer:${name}`, renderer); }
    registerInteraction(name, interaction) { return this.#registry.register(`interaction:${name}`, interaction); }
    registerBlueprint(name, blueprint) { return this.#registry.register(`blueprint:${name}`, blueprint); }
}
