import { CANVAS_MODULE_KEY } from "./constants.js";
import { CanvasService } from "./canvas_service.js";

/**
 * Módulo de Canvas registrable en BuilderApp.
 * No depende de DOM, Django, Renderer ni del modelo de negocio.
 */
export class CanvasModule {
    key = CANVAS_MODULE_KEY;
    service = null;

    constructor(options = {}) {
        this.options = Object.freeze({
            ensureOne: options.ensureOne !== false,
            initialCanvas: options.initialCanvas || {},
        });
    }

    async start({ app }) {
        if (this.service) return this;
        this.service = new CanvasService({ app });
        if (this.options.ensureOne) {
            const first = this.service.ensureOne(this.options.initialCanvas);
            this.service.select(first.id);
        }
        return this;
    }

    async destroy() {
        this.service?.destroy();
        this.service = null;
    }
}

export function registerCanvasModule(app, options = {}) {
    if (!app || typeof app.register !== "function") {
        throw new TypeError("registerCanvasModule requiere BuilderApp.");
    }
    const module = new CanvasModule(options);
    app.register(CANVAS_MODULE_KEY, module, { replace: options.replace === true });
    return module;
}
