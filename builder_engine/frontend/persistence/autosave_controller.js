import { DEFAULT_AUTOSAVE_DELAY_MS } from "./constants.js";

export class AutosaveController {
    #delay;
    #save;
    #timer = null;
    #pending = false;
    #destroyed = false;

    constructor(options = {}) {
        if (typeof options.save !== "function") {
            throw new TypeError("AutosaveController requiere save().");
        }
        this.#save = options.save;
        this.#delay = positiveInteger(options.delay, DEFAULT_AUTOSAVE_DELAY_MS);
    }

    schedule() {
        if (this.#destroyed) return;
        this.#pending = true;
        clearTimeout(this.#timer);
        this.#timer = setTimeout(() => this.flush(), this.#delay);
    }

    cancel() {
        clearTimeout(this.#timer);
        this.#timer = null;
        this.#pending = false;
    }

    async flush() {
        if (this.#destroyed || !this.#pending) return false;
        clearTimeout(this.#timer);
        this.#timer = null;
        this.#pending = false;
        await this.#save();
        return true;
    }

    destroy() {
        this.cancel();
        this.#destroyed = true;
    }
}

function positiveInteger(value, fallback) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}
