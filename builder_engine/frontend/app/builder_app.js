import { BuilderRegistry } from "./registry.js";
import { normalizeBuilderConfig } from "./config.js";
import { BuilderDocument, createDocument } from "../document/index.js";

/**
 * Kernel del DIRTEC Builder Engine.
 * Coordina servicios inyectados sin conocer Canvas, Django o Renderer concretos.
 */
export class BuilderApp {
    static async start(options = {}) {
        const app = new BuilderApp(options);
        await app.start();
        return app;
    }

    #config;
    #registry;
    #document;
    #started = false;
    #dirty = false;
    #listeners = new Set();

    constructor(options = {}) {
        this.#config = normalizeBuilderConfig(options);
        this.#registry = options.registry instanceof BuilderRegistry
            ? options.registry
            : new BuilderRegistry();
        this.#document = new BuilderDocument(options.document || createDocument({
            metadata: { eventId: this.#config.eventId },
        }));
    }

    async start() {
        if (this.#started) return this;
        for (const name of this.#registry.list()) {
            await this.#registry.get(name)?.start?.({ app: this, config: this.#config });
        }
        this.#started = true;
        this.#emit("app:started");
        return this;
    }

    get config() { return this.#config; }
    get registry() { return this.#registry; }
    get isStarted() { return this.#started; }
    get isDirty() { return this.#dirty; }
    getDocument() { return this.#document.value; }

    register(name, implementation, options) {
        return this.#registry.register(name, implementation, options);
    }

    updateDocument(mutator, meta = {}) {
        this.#document.update(mutator);
        this.#dirty = true;
        this.#emit("document:changed", meta);
        return this.getDocument();
    }

    markSaved() {
        this.#dirty = false;
        this.#emit("document:saved");
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        return () => this.#listeners.delete(listener);
    }

    async destroy() {
        const names = this.#registry.list().reverse();
        for (const name of names) {
            await this.#registry.get(name)?.destroy?.({ app: this });
        }
        this.#listeners.clear();
        this.#started = false;
    }

    #emit(type, payload = {}) {
        const event = Object.freeze({ type, payload, app: this });
        for (const listener of this.#listeners) listener(event);
    }
}
