
export class SelectionState {
    #selected = [];
    #primary = null;

    get selectedIds() { return [...this.#selected]; }
    get primaryId() { return this.#primary; }

    select(id, { additive = false } = {}) {
        if (!id) return this.snapshot();
        if (!additive) this.#selected = [];
        if (!this.#selected.includes(id)) this.#selected.push(id);
        this.#primary = id;
        return this.snapshot();
    }

    toggle(id) {
        if (!id) return this.snapshot();
        if (this.#selected.includes(id)) {
            this.#selected = this.#selected.filter(value => value !== id);
            this.#primary = this.#selected.at(-1) || null;
        } else {
            this.#selected.push(id);
            this.#primary = id;
        }
        return this.snapshot();
    }

    clear() {
        this.#selected = [];
        this.#primary = null;
        return this.snapshot();
    }

    contains(id) { return this.#selected.includes(id); }

    snapshot() {
        return Object.freeze({
            selectedIds: [...this.#selected],
            primaryId: this.#primary,
        });
    }
}
