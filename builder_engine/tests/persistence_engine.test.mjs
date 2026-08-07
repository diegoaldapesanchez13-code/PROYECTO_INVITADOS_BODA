import assert from "node:assert/strict";
import test from "node:test";
import {
    PersistenceService,
    WorkspaceState,
    createMemoryPersistenceAdapter,
    createDjangoPersistenceAdapter,
} from "../frontend/persistence/index.js";

function createFakeApp(document = { metadata: {}, canvases: [] }) {
    let value = structuredClone(document);
    let dirty = false;
    const listeners = new Set();
    return {
        get isDirty() { return dirty; },
        getDocument() { return structuredClone(value); },
        replaceDocument(next, meta = {}) {
            value = structuredClone(next);
            if (meta.markDirty !== false) dirty = true;
            for (const listener of listeners) {
                listener({ type: "document:replaced", payload: meta });
            }
        },
        update(mutator, meta = {}) {
            const draft = structuredClone(value);
            mutator(draft);
            value = draft;
            dirty = true;
            for (const listener of listeners) {
                listener({ type: "document:changed", payload: meta });
            }
        },
        markSaved() {
            dirty = false;
            for (const listener of listeners) {
                listener({ type: "document:saved", payload: {} });
            }
        },
        subscribe(listener) {
            listeners.add(listener);
            return () => listeners.delete(listener);
        },
    };
}

test("PersistenceService guarda y limpia dirty state", async () => {
    const app = createFakeApp({ metadata: { name: "Inicial" }, canvases: [] });
    const adapter = createMemoryPersistenceAdapter();
    const service = new PersistenceService({ app, port: adapter, autosave: false }).start();

    app.update((document) => { document.metadata.name = "Cambio"; });
    assert.equal(app.isDirty, true);
    await service.save({ reason: "manual" });
    assert.equal(app.isDirty, false);
    assert.equal(adapter.inspect().draft.metadata.name, "Cambio");
    service.destroy();
});

test("PersistenceService carga documento sin marcarlo como sucio", async () => {
    const saved = { metadata: { name: "Guardado" }, canvases: [] };
    const app = createFakeApp({ metadata: { name: "Vacío" }, canvases: [] });
    const service = new PersistenceService({
        app,
        port: createMemoryPersistenceAdapter(saved),
        autosave: false,
    }).start();

    await service.load();
    assert.equal(app.getDocument().metadata.name, "Guardado");
    assert.equal(app.isDirty, false);
    service.destroy();
});

test("Publicar guarda antes de publicar", async () => {
    const calls = [];
    const app = createFakeApp({ metadata: { name: "Documento" }, canvases: [] });
    const service = new PersistenceService({
        app,
        autosave: false,
        port: {
            async load() { return { document: app.getDocument() }; },
            async save({ document }) { calls.push(["save", document.metadata.name]); return { ok: true }; },
            async publish({ document }) { calls.push(["publish", document.metadata.name]); return { ok: true }; },
        },
    }).start();

    app.update((document) => { document.metadata.name = "Publicado"; });
    await service.publish();
    assert.deepEqual(calls.map((item) => item[0]), ["save", "publish"]);
    service.destroy();
});

test("WorkspaceState permanece separado del Documento", () => {
    const workspace = new WorkspaceState({ zoom: 1.5, selectedNodeId: "n-1" });
    workspace.update((state) => {
        state.activeInspectorTab = "typography";
    });
    assert.equal(workspace.value.zoom, 1.5);
    assert.equal(workspace.value.selectedNodeId, "n-1");
    assert.equal(workspace.value.activeInspectorTab, "typography");
});

test("Django adapter usa endpoints inyectados y CSRF", async () => {
    const calls = [];
    const adapter = createDjangoPersistenceAdapter({
        endpoints: {
            load: "/builder/load/",
            save: "/builder/save/",
            publish: "/builder/publish/",
        },
        csrfToken: "token-123",
        fetchImpl: async (url, options) => {
            calls.push({ url, options });
            return {
                ok: true,
                status: 200,
                async json() { return { ok: true, document: { canvases: [] } }; },
            };
        },
    });

    await adapter.save({ document: { canvases: [] }, reason: "manual" });
    assert.equal(calls[0].url, "/builder/save/");
    assert.equal(calls[0].options.headers["X-CSRFToken"], "token-123");
    assert.equal(JSON.parse(calls[0].options.body).reason, "manual");
});

test("PersistenceService evita guardados paralelos duplicados", async () => {
    let saves = 0;
    let resolveSave;
    const pending = new Promise((resolve) => { resolveSave = resolve; });
    const app = createFakeApp({ metadata: {}, canvases: [] });
    const service = new PersistenceService({
        app,
        autosave: false,
        port: {
            async load() { return { document: app.getDocument() }; },
            async save() { saves += 1; await pending; return { ok: true }; },
            async publish() { return { ok: true }; },
        },
    }).start();

    const first = service.save();
    const second = service.save();
    resolveSave();
    await Promise.all([first, second]);
    assert.equal(saves, 1);
    service.destroy();
});
