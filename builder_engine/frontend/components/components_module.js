import { COMPONENTS_MODULE_NAME } from "./constants.js";
import { ComponentRegistry } from "./component_registry.js";
import { ComponentFactory } from "./component_factory.js";
import { BlueprintRegistry } from "./blueprint_registry.js";
import { ComponentsService } from "./components_service.js";
import { builtinComponentDefinitions } from "./builtin_definitions.js";
import { createCountdownBlueprint } from "./blueprints/countdown_blueprint.js";

export class ComponentsModule {
    key = COMPONENTS_MODULE_NAME;
    version = "1.0.0";
    dependencies = Object.freeze(["canvas"]);
    registry;
    factory;
    blueprints;
    service;

    constructor(options = {}) {
        this.options = options;
        this.registry = options.registry || new ComponentRegistry();
        this.factory = options.factory || new ComponentFactory(this.registry, options);
        this.blueprints = options.blueprints || new BlueprintRegistry();
        this.service = null;
    }

    start({ app }) {
        if (this.service) return this;
        this.registry.registerMany(
            this.options.definitions || builtinComponentDefinitions(),
            { replace: this.options.replaceBuiltins === true },
        );
        if (!this.blueprints.get("countdown", { required: false })) {
            this.blueprints.register(createCountdownBlueprint(this.factory));
        }
        this.service = new ComponentsService({
            app,
            registry: this.registry,
            factory: this.factory,
            blueprints: this.blueprints,
        });
        return this;
    }

    destroy() {
        this.service = null;
    }
}

export function registerComponentsModule(app, options = {}) {
    if (!app?.register) throw new TypeError("registerComponentsModule requiere BuilderApp.");
    const module = new ComponentsModule(options);
    app.register(COMPONENTS_MODULE_NAME, module, { replace: options.replace === true });
    return module;
}
