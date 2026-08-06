import { PERSISTENCE_MODULE_NAME } from "./constants.js";
import { PersistenceService } from "./persistence_service.js";
import { WorkspaceState } from "./workspace_state.js";

export class PersistenceModule {
    key = PERSISTENCE_MODULE_NAME;
    version = "1.0.0";
    dependencies = Object.freeze(["history", "assets", "canvas", "components", "interaction"]);
    service = null;
    workspace = null;

    constructor(options = {}) {
        this.options = options;
    }

    start({ app }) {
        if (this.service) return this;
        this.workspace = new WorkspaceState(this.options.workspaceState);
        this.service = new PersistenceService({
            app,
            port: this.options.port,
            autosave: this.options.autosave !== false,
            autosaveDelay: this.options.autosaveDelay,
        });
        this.service.start();
        return this;
    }

    destroy() {
        this.service?.destroy();
        this.service = null;
        this.workspace = null;
    }
}

export function registerPersistenceModule(app, options = {}) {
    if (!app?.register) throw new TypeError("registerPersistenceModule requiere BuilderApp.");
    const module = new PersistenceModule(options);
    app.register(PERSISTENCE_MODULE_NAME, module, { replace: options.replace === true });
    return module;
}
