import { HISTORY_MODULE_NAME } from "./constants.js";
import { HistoryService } from "./history_service.js";

export class HistoryModule {
    constructor(app, options = {}) {
        this.name = HISTORY_MODULE_NAME;
        this.service = new HistoryService(app, options);
    }

    start() {
        this.service.start();
        return this;
    }

    destroy() {
        this.service.destroy();
    }
}

export function registerHistoryModule(app, options = {}) {
    const module = new HistoryModule(app, options);
    app.register(HISTORY_MODULE_NAME, module, { replace: options.replace === true });
    return module;
}
