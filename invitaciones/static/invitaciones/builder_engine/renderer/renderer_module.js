import { DEFAULT_RENDER_MODE, RENDERER_MODULE_KEY } from "./constants.js";
import { registerDefaultRenderers } from "./default_renderers.js";
import { RendererRegistry } from "./renderer_registry.js";
import { RendererService } from "./renderer_service.js";

export class RendererModule {
    key = RENDERER_MODULE_KEY;
    registry;
    service = null;

    constructor(options = {}) {
        this.options = Object.freeze({
            mode: options.mode || DEFAULT_RENDER_MODE,
            defaultRenderers: options.defaultRenderers !== false,
        });
        this.registry = options.registry instanceof RendererRegistry
            ? options.registry
            : new RendererRegistry();
        if (this.options.defaultRenderers) registerDefaultRenderers(this.registry);
        for (const entry of options.renderers || []) {
            this.registry.register(entry.type, entry.renderer, { replace: entry.replace === true });
        }
    }

    async start({ app }) {
        if (this.service) return this;
        this.service = new RendererService({
            app,
            registry: this.registry,
            mode: this.options.mode,
        });
        return this;
    }

    async destroy() {
        this.service?.destroy();
        this.service = null;
    }
}

export function registerRendererModule(app, options = {}) {
    if (!app || typeof app.register !== "function") {
        throw new TypeError("registerRendererModule requiere BuilderApp.");
    }
    const module = new RendererModule(options);
    app.register(RENDERER_MODULE_KEY, module, { replace: options.replace === true });
    return module;
}
