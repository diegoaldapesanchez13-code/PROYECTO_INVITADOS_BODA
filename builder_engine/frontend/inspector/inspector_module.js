import { INSPECTOR_MODULE_KEY } from "./constants.js";
import { InspectorRegistry } from "./inspector_registry.js";
import { InspectorService } from "./inspector_service.js";

export class InspectorModule {
    key = INSPECTOR_MODULE_KEY;
    registry;
    service = null;

    constructor(options = {}) {
        this.registry = options.registry instanceof InspectorRegistry
            ? options.registry
            : new InspectorRegistry();
        for (const panel of options.panels || []) this.registry.register(panel);
    }

    async start({ app }) {
        if (this.service) return this;
        this.service = new InspectorService({ app, registry: this.registry });
        return this;
    }

    async destroy() {
        this.service?.destroy();
        this.service = null;
    }
}

export function registerInspectorModule(app, options = {}) {
    if (!app || typeof app.register !== "function") {
        throw new TypeError("registerInspectorModule requiere BuilderApp.");
    }
    const module = new InspectorModule(options);
    app.register(INSPECTOR_MODULE_KEY, module, { replace: options.replace === true });
    return module;
}
