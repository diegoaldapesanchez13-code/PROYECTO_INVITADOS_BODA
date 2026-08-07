import { normalizeRenderMode } from "./constants.js";
import { createRenderCanvas, createRenderResult } from "./render_tree.js";
import { RendererRegistry } from "./renderer_registry.js";

export class RendererService {
    #app;
    #registry;
    #mode;
    #lastResult = null;
    #listeners = new Set();

    constructor({ app, registry, mode } = {}) {
        if (!app || typeof app.getDocument !== "function") {
            throw new TypeError("RendererService requiere BuilderApp.");
        }
        this.#app = app;
        this.#registry = registry instanceof RendererRegistry ? registry : new RendererRegistry();
        this.#mode = normalizeRenderMode(mode);
    }

    get mode() { return this.#mode; }
    get lastResult() { return this.#lastResult; }
    get registry() { return this.#registry; }

    setMode(mode) {
        this.#mode = normalizeRenderMode(mode);
        return this.#mode;
    }

    render(options = {}) {
        const document = options.document || this.#app.getDocument();
        const mode = normalizeRenderMode(options.mode || this.#mode);
        const canvases = [...(document.canvases || [])]
            .sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
            .map((canvas) => this.#renderCanvas(canvas, { document, mode, options }));

        this.#lastResult = createRenderResult({
            mode,
            document,
            canvases,
            metadata: {
                renderedAt: new Date().toISOString(),
                canvasCount: canvases.length,
                editable: mode === "EDIT",
                interactive: mode !== "EDIT",
            },
        });
        this.#emit(this.#lastResult);
        return this.#lastResult;
    }

    renderCanvas(canvasId, options = {}) {
        const document = options.document || this.#app.getDocument();
        const canvas = (document.canvases || []).find((item) => item.id === canvasId);
        if (!canvas) throw new Error(`Lienzo no encontrado: ${canvasId}`);
        return this.#renderCanvas(canvas, {
            document,
            mode: normalizeRenderMode(options.mode || this.#mode),
            options,
        });
    }

    renderNode(node, context = {}) {
        if (!node || typeof node !== "object") throw new TypeError("Nodo inválido.");
        if (node.visible === false) return null;
        const mode = normalizeRenderMode(context.mode || this.#mode);
        const children = (node.children || node.nodes || [])
            .map((child) => this.renderNode(child, { ...context, mode, parent: node }))
            .filter(Boolean);
        const renderer = this.#registry.resolve(node.type || "UNKNOWN");
        const render = typeof renderer === "function" ? renderer : renderer.render.bind(renderer);
        return render(node, {
            ...context,
            app: this.#app,
            document: context.document || this.#app.getDocument(),
            mode,
            children,
            editable: mode === "EDIT",
            interactive: mode !== "EDIT",
        }, children);
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser función.");
        this.#listeners.add(listener);
        return () => this.#listeners.delete(listener);
    }

    destroy() {
        this.#listeners.clear();
        this.#lastResult = null;
    }

    #renderCanvas(canvas, context) {
        const children = (canvas.nodes || [])
            .map((node) => this.renderNode(node, { ...context, canvas }))
            .filter(Boolean);
        return createRenderCanvas(canvas, children);
    }

    #emit(result) {
        for (const listener of this.#listeners) listener(result);
    }
}
