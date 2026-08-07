export function createMemoryPersistenceAdapter(initialDocument = null) {
    let draft = clone(initialDocument);
    let published = null;

    return Object.freeze({
        async load() {
            if (!draft) throw new Error("No existe documento guardado.");
            return { document: clone(draft) };
        },
        async save({ document }) {
            draft = clone(document);
            return { ok: true, documentVersion: document.documentVersion };
        },
        async publish({ document }) {
            published = clone(document);
            return { ok: true, publishedAt: new Date().toISOString() };
        },
        inspect() {
            return { draft: clone(draft), published: clone(published) };
        },
    });
}

function clone(value) {
    if (value == null) return value;
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
