export class LayerTreeState {
    #expanded = new Set();
    #selectedId = null;
    #drag = null;

    constructor(options = {}) {
        for (const id of options.expandedIds || []) this.#expanded.add(id);
        this.#selectedId = options.selectedId || null;
    }

    get selectedId() { return this.#selectedId; }
    get expandedIds() { return new Set(this.#expanded); }
    get dragState() { return this.#drag ? { ...this.#drag } : null; }

    select(nodeId) {
        this.#selectedId = nodeId || null;
        return this.snapshot();
    }

    toggleExpanded(nodeId) {
        if (this.#expanded.has(nodeId)) this.#expanded.delete(nodeId);
        else this.#expanded.add(nodeId);
        return this.snapshot();
    }

    expand(nodeId) {
        this.#expanded.add(nodeId);
        return this.snapshot();
    }

    collapse(nodeId) {
        this.#expanded.delete(nodeId);
        return this.snapshot();
    }

    beginDrag(nodeId) {
        this.#drag = { nodeId, targetId: null, placement: null };
        return this.dragState;
    }

    updateDrag(targetId, placement) {
        if (!this.#drag) return null;
        this.#drag.targetId = targetId || null;
        this.#drag.placement = placement || null;
        return this.dragState;
    }

    endDrag() {
        const completed = this.dragState;
        this.#drag = null;
        return completed;
    }

    cancelDrag() {
        this.#drag = null;
    }

    snapshot() {
        return Object.freeze({
            selectedId: this.#selectedId,
            expandedIds: [...this.#expanded],
            drag: this.dragState,
        });
    }
}
