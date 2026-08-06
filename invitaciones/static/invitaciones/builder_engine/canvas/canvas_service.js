import { createCanvas, normalizeCanvas, normalizeCanvasCollection } from "./canvas_schema.js";

export class CanvasService {
    #app;
    #selectedId = null;
    #listeners = new Set();

    constructor({ app } = {}) {
        if (!app || typeof app.updateDocument !== "function") {
            throw new TypeError("CanvasService requiere una instancia de BuilderApp.");
        }
        this.#app = app;
    }

    list() {
        return normalizeCanvasCollection(this.#app.getDocument().canvases);
    }

    get(id) {
        return this.list().find((canvas) => canvas.id === String(id)) || null;
    }

    get selectedId() {
        return this.#selectedId;
    }

    get selected() {
        return this.#selectedId ? this.get(this.#selectedId) : null;
    }

    ensureOne(options = {}) {
        if (this.list().length) return this.list()[0];
        return this.create(options);
    }

    create(options = {}) {
        const canvases = this.list();
        const canvas = createCanvas({
            ...options,
            order: canvases.length,
            name: options.name || `Lienzo ${canvases.length + 1}`,
        });
        this.#replace([...canvases, canvas], "canvas:created", { canvasId: canvas.id });
        this.select(canvas.id);
        return this.get(canvas.id);
    }

    update(id, patch = {}) {
        const current = this.get(id);
        if (!current) return null;
        const next = normalizeCanvas({ ...current, ...patch, id: current.id, order: current.order });
        const canvases = this.list().map((canvas) => canvas.id === current.id ? next : canvas);
        this.#replace(canvases, "canvas:updated", { canvasId: current.id });
        return this.get(current.id);
    }

    duplicate(id, options = {}) {
        const current = this.get(id);
        if (!current) return null;
        const canvases = this.list();
        const clone = createCanvas({
            ...current,
            id: options.id,
            name: options.name || `${current.name} copia`,
            order: current.order + 1,
            nodes: current.nodes,
            metadata: { ...current.metadata, duplicatedFrom: current.id },
        });
        canvases.splice(current.order + 1, 0, clone);
        this.#replace(canvases, "canvas:duplicated", { canvasId: clone.id, sourceId: current.id });
        this.select(clone.id);
        return this.get(clone.id);
    }

    remove(id, { allowEmpty = false } = {}) {
        const current = this.get(id);
        if (!current || current.locked) return false;
        const canvases = this.list();
        if (!allowEmpty && canvases.length <= 1) return false;
        const index = canvases.findIndex((canvas) => canvas.id === current.id);
        const nextCanvases = canvases.filter((canvas) => canvas.id !== current.id);
        this.#replace(nextCanvases, "canvas:removed", { canvasId: current.id });
        if (this.#selectedId === current.id) {
            const next = this.list()[Math.min(index, this.list().length - 1)] || null;
            this.select(next?.id || null);
        }
        return true;
    }

    move(id, targetIndex) {
        const canvases = this.list();
        const fromIndex = canvases.findIndex((canvas) => canvas.id === String(id));
        if (fromIndex < 0) return null;
        const toIndex = Math.min(Math.max(Number(targetIndex) || 0, 0), canvases.length - 1);
        const [canvas] = canvases.splice(fromIndex, 1);
        canvases.splice(toIndex, 0, canvas);
        this.#replace(canvases, "canvas:moved", { canvasId: canvas.id, fromIndex, toIndex });
        return this.get(canvas.id);
    }

    moveUp(id) {
        const canvas = this.get(id);
        return canvas ? this.move(id, canvas.order - 1) : null;
    }

    moveDown(id) {
        const canvas = this.get(id);
        return canvas ? this.move(id, canvas.order + 1) : null;
    }

    select(id) {
        const next = id == null ? null : this.get(id);
        this.#selectedId = next?.id || null;
        this.#emit("canvas:selected", { canvasId: this.#selectedId, canvas: next });
        return next;
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        return () => this.#listeners.delete(listener);
    }

    destroy() {
        this.#listeners.clear();
        this.#selectedId = null;
    }

    #replace(canvases, type, payload) {
        const normalized = normalizeCanvasCollection(
            canvases.map((canvas, index) => ({ ...canvas, order: index })),
        );
        this.#app.updateDocument((document) => {
            document.canvases = normalized;
        }, { type, ...payload });
        this.#emit(type, payload);
    }

    #emit(type, payload = {}) {
        const event = Object.freeze({ type, payload, service: this });
        for (const listener of this.#listeners) listener(event);
    }
}
