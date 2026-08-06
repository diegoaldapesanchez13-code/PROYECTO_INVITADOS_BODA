import {
    PERSISTENCE_STATUS,
} from "./constants.js";
import { requirePersistencePort } from "./ports/persistence_port.js";
import { AutosaveController } from "./autosave_controller.js";

export class PersistenceService {
    #app;
    #port;
    #autosave;
    #status = PERSISTENCE_STATUS.IDLE;
    #lastSavedAt = null;
    #lastPublishedAt = null;
    #lastError = null;
    #listeners = new Set();
    #unsubscribe = null;
    #savePromise = null;
    #publishPromise = null;

    constructor({ app, port, autosaveDelay, autosave = true }) {
        if (!app?.getDocument || !app?.replaceDocument || !app?.markSaved) {
            throw new TypeError("PersistenceService requiere BuilderApp compatible.");
        }
        this.#app = app;
        this.#port = requirePersistencePort(port);
        this.#autosave = autosave
            ? new AutosaveController({
                delay: autosaveDelay,
                save: () => this.save({ reason: "autosave" }),
            })
            : null;
    }

    start() {
        if (this.#unsubscribe) return this;
        this.#unsubscribe = this.#app.subscribe((event) => {
            if (event.type === "document:changed" || event.type === "document:replaced") {
                if (!event.payload?.persistenceLoad && !event.payload?.historyReplay) {
                    this.#autosave?.schedule();
                }
            }
            if (event.type === "document:saved") {
                this.#emit();
            }
        });
        this.#emit();
        return this;
    }

    async load(context = {}) {
        this.#setStatus(PERSISTENCE_STATUS.LOADING);
        try {
            const result = await this.#port.load(context);
            const document = result?.document ?? result;
            this.#app.replaceDocument(document, {
                persistenceLoad: true,
                markDirty: false,
                source: "persistence",
            });
            this.#app.markSaved();
            this.#setStatus(PERSISTENCE_STATUS.SAVED);
            return this.#app.getDocument();
        } catch (error) {
            this.#fail(error);
            throw error;
        }
    }

    async save(options = {}) {
        if (this.#savePromise) return this.#savePromise;
        this.#autosave?.cancel();
        this.#savePromise = this.#performSave(options)
            .finally(() => { this.#savePromise = null; });
        return this.#savePromise;
    }

    async #performSave(options) {
        this.#setStatus(PERSISTENCE_STATUS.SAVING);
        try {
            const document = this.#app.getDocument();
            const result = await this.#port.save({
                document,
                reason: options.reason || "manual",
                context: options.context || {},
            });
            this.#lastSavedAt = new Date().toISOString();
            this.#lastError = null;
            this.#app.markSaved();
            this.#setStatus(PERSISTENCE_STATUS.SAVED);
            return result;
        } catch (error) {
            this.#fail(error);
            throw error;
        }
    }

    async publish(options = {}) {
        if (this.#publishPromise) return this.#publishPromise;
        this.#publishPromise = this.#performPublish(options)
            .finally(() => { this.#publishPromise = null; });
        return this.#publishPromise;
    }

    async #performPublish(options) {
        await this.save({ reason: "before-publish", context: options.context });
        this.#setStatus(PERSISTENCE_STATUS.PUBLISHING);
        try {
            const result = await this.#port.publish({
                document: this.#app.getDocument(),
                context: options.context || {},
            });
            this.#lastPublishedAt = new Date().toISOString();
            this.#lastError = null;
            this.#setStatus(PERSISTENCE_STATUS.PUBLISHED);
            return result;
        } catch (error) {
            this.#fail(error);
            throw error;
        }
    }

    async flushAutosave() {
        return this.#autosave?.flush() ?? false;
    }

    state() {
        return Object.freeze({
            status: this.#status,
            dirty: this.#app.isDirty,
            lastSavedAt: this.#lastSavedAt,
            lastPublishedAt: this.#lastPublishedAt,
            lastError: this.#lastError,
        });
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        listener(this.state());
        return () => this.#listeners.delete(listener);
    }

    destroy() {
        this.#unsubscribe?.();
        this.#unsubscribe = null;
        this.#autosave?.destroy();
        this.#listeners.clear();
    }

    #setStatus(status) {
        this.#status = status;
        this.#emit();
    }

    #fail(error) {
        this.#lastError = {
            message: error instanceof Error ? error.message : String(error),
            at: new Date().toISOString(),
        };
        this.#setStatus(PERSISTENCE_STATUS.ERROR);
    }

    #emit() {
        const state = this.state();
        for (const listener of this.#listeners) listener(state);
    }
}
