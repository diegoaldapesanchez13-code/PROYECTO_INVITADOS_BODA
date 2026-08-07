import { createDocument, normalizeDocument, validateDocument } from "./schema.js";

export class BuilderDocument {
    #value;

    constructor(raw = createDocument()) {
        this.replace(raw);
    }

    get value() {
        return structuredCloneSafe(this.#value);
    }

    replace(raw) {
        const normalized = normalizeDocument(raw);
        const result = validateDocument(normalized);
        if (!result.valid) throw new Error(result.errors.join("\n"));
        this.#value = normalized;
        return this;
    }

    update(mutator) {
        if (typeof mutator !== "function") throw new TypeError("mutator debe ser una función.");
        const draft = this.value;
        const returned = mutator(draft);
        const next = returned && typeof returned === "object" ? returned : draft;
        next.documentVersion = Number(next.documentVersion || 0) + 1;
        next.metadata = { ...(next.metadata || {}), updatedAt: new Date().toISOString() };
        return this.replace(next);
    }
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
