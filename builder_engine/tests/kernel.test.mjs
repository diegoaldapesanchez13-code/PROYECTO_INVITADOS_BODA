import test from "node:test";
import assert from "node:assert/strict";
import { BuilderApp, BuilderRegistry } from "../frontend/app/index.js";
import { createDocument, serializeDocument, deserializeDocument } from "../frontend/document/index.js";
import { BuilderSDK } from "../frontend/sdk/index.js";

test("BuilderRegistry registra y resuelve módulos", () => {
    const registry = new BuilderRegistry();
    const service = {};
    registry.register("renderer", service);
    assert.equal(registry.get("renderer"), service);
    assert.deepEqual(registry.list(), ["renderer"]);
});

test("BuilderApp inicia servicios y controla dirty state", async () => {
    const calls = [];
    const registry = new BuilderRegistry();
    registry.register("service", {
        start: () => calls.push("start"),
        destroy: () => calls.push("destroy"),
    });
    const app = await BuilderApp.start({ registry, document: createDocument() });
    app.updateDocument((document) => {
        document.metadata.name = "Invitación";
    });
    assert.equal(app.isDirty, true);
    assert.equal(app.getDocument().metadata.name, "Invitación");
    app.markSaved();
    assert.equal(app.isDirty, false);
    await app.destroy();
    assert.deepEqual(calls, ["start", "destroy"]);
});

test("Document Engine serializa y restaura el contrato", () => {
    const source = createDocument({ canvases: [{ id: "canvas-1" }] });
    const restored = deserializeDocument(serializeDocument(source));
    assert.equal(restored.schemaVersion, 1);
    assert.equal(restored.canvases[0].id, "canvas-1");
});

test("BuilderSDK registra extensiones sin tocar el Kernel", () => {
    const sdk = new BuilderSDK();
    sdk.registerComponent("text", { type: "TEXT" });
    sdk.registerTheme("default", { id: "default" });
    assert.equal(sdk.registry.has("component:text"), true);
    assert.equal(sdk.registry.has("theme:default"), true);
});
