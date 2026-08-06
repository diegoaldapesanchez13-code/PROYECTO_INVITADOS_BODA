import {
    DEFAULT_HISTORY_LIMIT,
    DEFAULT_MERGE_WINDOW_MS,
} from "./constants.js";
import { createSnapshot, restoreSnapshot } from "./snapshot.js";

export class HistoryService {
    #app;
    #limit;
    #mergeWindowMs;
    #entries = [];
    #index = -1;
    #transaction = null;
    #unsubscribe = null;
    #replaying = false;
    #listeners = new Set();

    constructor(app, options = {}) {
        if (!app?.getDocument || !app?.replaceDocument) {
            throw new TypeError("HistoryService requiere una instancia de BuilderApp compatible.");
        }
        this.#app = app;
        this.#limit = positiveInteger(options.limit, DEFAULT_HISTORY_LIMIT);
        this.#mergeWindowMs = positiveInteger(options.mergeWindowMs, DEFAULT_MERGE_WINDOW_MS);
    }

    start() {
        if (this.#unsubscribe) return this;
        this.#entries = [createSnapshot(this.#app.getDocument(), { label: "Estado inicial" })];
        this.#index = 0;
        this.#unsubscribe = this.#app.subscribe((event) => this.#onAppEvent(event));
        this.#emit();
        return this;
    }

    destroy() {
        this.#unsubscribe?.();
        this.#unsubscribe = null;
        this.#listeners.clear();
        this.#transaction = null;
    }

    get canUndo() { return this.#index > 0; }
    get canRedo() { return this.#index >= 0 && this.#index < this.#entries.length - 1; }
    get index() { return this.#index; }
    get length() { return this.#entries.length; }
    get inTransaction() { return Boolean(this.#transaction); }

    timeline() {
        return this.#entries.map((entry, index) => ({
            id: entry.id,
            label: entry.label,
            mergeKey: entry.mergeKey,
            createdAt: entry.createdAt,
            current: index === this.#index,
            index,
        }));
    }

    beginTransaction(meta = {}) {
        if (this.#transaction) throw new Error("Ya existe una transacción activa.");
        this.#transaction = {
            label: String(meta.label || "Transacción"),
            mergeKey: meta.mergeKey ? String(meta.mergeKey) : null,
            before: this.#app.getDocument(),
            changed: false,
        };
        return this;
    }

    commitTransaction(meta = {}) {
        if (!this.#transaction) return false;
        const transaction = this.#transaction;
        this.#transaction = null;
        if (!transaction.changed) return false;
        this.#record(this.#app.getDocument(), {
            label: meta.label || transaction.label,
            mergeKey: meta.mergeKey || transaction.mergeKey,
            force: true,
        });
        return true;
    }

    cancelTransaction() {
        if (!this.#transaction) return false;
        const document = this.#transaction.before;
        this.#transaction = null;
        this.#replaceFromHistory(document, { action: "cancel-transaction" });
        return true;
    }

    undo() {
        if (!this.canUndo) return false;
        this.#index -= 1;
        this.#replaceFromHistory(restoreSnapshot(this.#entries[this.#index]), { action: "undo" });
        this.#emit();
        return true;
    }

    redo() {
        if (!this.canRedo) return false;
        this.#index += 1;
        this.#replaceFromHistory(restoreSnapshot(this.#entries[this.#index]), { action: "redo" });
        this.#emit();
        return true;
    }

    goTo(index) {
        const target = Number(index);
        if (!Number.isInteger(target) || target < 0 || target >= this.#entries.length) {
            throw new RangeError("Índice de historial fuera de rango.");
        }
        if (target === this.#index) return false;
        this.#index = target;
        this.#replaceFromHistory(restoreSnapshot(this.#entries[target]), { action: "time-travel" });
        this.#emit();
        return true;
    }

    clear() {
        this.#entries = [createSnapshot(this.#app.getDocument(), { label: "Estado actual" })];
        this.#index = 0;
        this.#transaction = null;
        this.#emit();
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        listener(this.state());
        return () => this.#listeners.delete(listener);
    }

    state() {
        return Object.freeze({
            canUndo: this.canUndo,
            canRedo: this.canRedo,
            index: this.#index,
            length: this.#entries.length,
            inTransaction: this.inTransaction,
            timeline: this.timeline(),
        });
    }

    #onAppEvent(event) {
        if (this.#replaying) return;
        if (event.type !== "document:changed" && event.type !== "document:replaced") return;
        if (event.payload?.historyReplay) return;

        if (this.#transaction) {
            this.#transaction.changed = true;
            return;
        }

        this.#record(this.#app.getDocument(), {
            label: event.payload?.label || "Cambio",
            mergeKey: event.payload?.mergeKey || null,
        });
    }

    #record(document, meta = {}) {
        const now = Date.now();
        const current = this.#entries[this.#index];
        const mayMerge = !meta.force
            && meta.mergeKey
            && current?.mergeKey === String(meta.mergeKey)
            && now - current.createdAt <= this.#mergeWindowMs;

        const snapshot = createSnapshot(document, {
            label: meta.label,
            mergeKey: meta.mergeKey,
            createdAt: now,
        });

        if (mayMerge) {
            this.#entries[this.#index] = snapshot;
        } else {
            this.#entries = this.#entries.slice(0, this.#index + 1);
            this.#entries.push(snapshot);
            if (this.#entries.length > this.#limit) {
                this.#entries.splice(0, this.#entries.length - this.#limit);
            }
            this.#index = this.#entries.length - 1;
        }
        this.#emit();
    }

    #replaceFromHistory(document, meta = {}) {
        this.#replaying = true;
        try {
            this.#app.replaceDocument(document, {
                ...meta,
                historyReplay: true,
                markDirty: true,
            });
        } finally {
            this.#replaying = false;
        }
    }

    #emit() {
        const state = this.state();
        for (const listener of this.#listeners) listener(state);
    }
}

function positiveInteger(value, fallback) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}
