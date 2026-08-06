import { ASSETS_MODULE_KEY } from "./constants.js";
import { AssetService } from "./asset_service.js";

export class AssetsModule {
    key = ASSETS_MODULE_KEY;
    service = null;

    constructor(options = {}) {
        this.options = options;
    }

    async start({ app }) {
        if (this.service) return this;
        this.service = new AssetService({
            app,
            uploader: this.options.uploader || null,
            deleter: this.options.deleter || null,
        });
        return this;
    }

    async destroy() {
        this.service?.destroy();
        this.service = null;
    }
}

export function registerAssetsModule(app, options = {}) {
    if (!app || typeof app.register !== "function") throw new TypeError("registerAssetsModule requiere BuilderApp.");
    const module = new AssetsModule(options);
    app.register(ASSETS_MODULE_KEY, module, { replace: options.replace === true });
    return module;
}
