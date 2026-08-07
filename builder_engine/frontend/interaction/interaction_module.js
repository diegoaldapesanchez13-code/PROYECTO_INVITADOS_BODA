import {
    INTERACTION_MODULE_NAME,
    INTERACTION_TYPES,
} from "./constants.js";
import { InteractionRegistry } from "./interaction_registry.js";
import { InteractionService } from "./interaction_service.js";
import {
    noneExecutor,
    urlExecutor,
    whatsappExecutor,
    mapsExecutor,
    canvasExecutor,
    componentEventExecutor,
} from "./executors/index.js";

export class InteractionModule {
    key = INTERACTION_MODULE_NAME;
    version = "1.0.0";
    dependencies = Object.freeze(["components"]);
    registry;
    service;

    constructor(options = {}) {
        this.options = options;
        this.registry = options.registry || new InteractionRegistry();
        this.service = null;
    }

    start({ app }) {
        if (this.service) return this;
        const executors = this.options.executors || [
            noneExecutor,
            urlExecutor,
            whatsappExecutor,
            mapsExecutor,
            canvasExecutor,
            componentEventExecutor,
        ];
        for (const executor of executors) {
            this.registry.register(executor.type, executor, {
                replace: this.options.replaceBuiltins === true,
            });
        }
        this.service = new InteractionService(this.registry, {
            contextFactory: () => ({
                app,
                document: app.getDocument(),
            }),
        });
        return this;
    }

    destroy() {
        this.service = null;
    }
}

export function registerInteractionModule(app, options = {}) {
    if (!app?.register) throw new TypeError("registerInteractionModule requiere BuilderApp.");
    const module = new InteractionModule(options);
    app.register(INTERACTION_MODULE_NAME, module, { replace: options.replace === true });
    return module;
}
