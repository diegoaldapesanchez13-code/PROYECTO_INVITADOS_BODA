import { BuilderState } from "../core/state.js";
import {
    createBuilderDocument,
    normalizeBuilderDocument,
    validateBuilderDocument,
} from "../document/schema.js";
import { ThemeManager } from "../themes/theme_manager.js";
import { normalizeBuilderConfig } from "./config.js";

export class BuilderApp {
    static async start(options = {}) {
        const app = new BuilderApp(options);
        await app.start();
        return app;
    }

    #options;
    #config;
    #document;
    #state;
    #themeManager;
    #runtime = null;
    #unsubscribe = null;
    #dirty = false;
    #started = false;

    constructor(options = {}) {
        this.#options = options;
        this.#config = normalizeBuilderConfig(options);
        this.#document = normalizeBuilderDocument(
            options.document || createBuilderDocument({
                metadata: { eventId: this.#config.eventId },
                assets: options.assets || [],
            })
        );
        this.#state = new BuilderState(this.#document.canvasDocument);
        this.#themeManager = new ThemeManager({ theme: this.#document.theme });
    }

    async start() {
        if (this.#started) return this;
        const validation = validateBuilderDocument(this.#document);
        if (!validation.valid) {
            throw new Error(validation.errors.join("\n"));
        }

        this.#unsubscribe = this.#state.subscribe((event) => {
            if (!String(event.type).startsWith("selection:")) {
                this.#dirty = true;
            }
        });

        if (typeof this.#options.createRuntime === "function") {
            this.#runtime = await this.#options.createRuntime({
                app: this,
                root: this.#options.root || null,
                state: this.#state,
                themeManager: this.#themeManager,
                assets: this.#document.assets,
                mode: this.#config.mode,
            });
        }

        this.#started = true;
        return this;
    }

    get state() { return this.#state; }
    get config() { return { ...this.#config }; }
    get theme() { return this.#themeManager.current; }
    get isDirty() { return this.#dirty; }
    get isStarted() { return this.#started; }

    getDocument() {
        return normalizeBuilderDocument({
            ...this.#document,
            metadata: {
                ...this.#document.metadata,
                eventId: this.#config.eventId ?? this.#document.metadata.eventId,
            },
            theme: this.#themeManager.current,
            canvasDocument: this.#state.document,
        });
    }

    async save() {
        const endpoints = this.#options.endpoints;
        if (!endpoints?.saveDocument) {
            throw new Error("No se configuró un endpoint para guardar el documento.");
        }
        const adapter = this.#options.documentAdapter;
        const document = this.getDocument();
        const payload = adapter?.toBackend ? adapter.toBackend(document) : { document };
        const result = await endpoints.saveDocument(payload.document || document);
        this.#document = normalizeBuilderDocument(result.document || payload.document || document);
        this.#dirty = false;
        return result;
    }

    async destroy() {
        this.#unsubscribe?.();
        await this.#runtime?.destroy?.();
        this.#runtime = null;
        this.#started = false;
    }
}
