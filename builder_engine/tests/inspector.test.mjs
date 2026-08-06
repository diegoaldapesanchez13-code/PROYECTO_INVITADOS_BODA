import assert from "node:assert/strict";
import test from "node:test";
import { BuilderApp } from "../frontend/app/index.js";
import { createDocument } from "../frontend/document/index.js";
import { registerInspectorModule } from "../frontend/inspector/index.js";

test("InspectorModule se registra y resuelve paneles por tipo", async () => {
    const document = createDocument({
        canvases: [{ id: "canvas-1", order: 0, nodes: [{ id: "text-1", type: "TEXT", content: { text: "Hola" } }] }],
    });
    const app = new BuilderApp({ document });
    const module = registerInspectorModule(app, {
        panels: [
            { id: "general", title: "General", order: 0 },
            { id: "text", title: "Texto", types: ["TEXT"], order: 10 },
            { id: "image", title: "Imagen", types: ["IMAGE"], order: 20 },
        ],
    });
    await app.start();
    module.service.select("text-1");
    assert.deepEqual(module.service.panels().map((panel) => panel.id), ["general", "text"]);
    await app.destroy();
});

test("InspectorService actualiza propiedades por ruta sin perder el resto del nodo", async () => {
    const document = createDocument({
        canvases: [{ id: "canvas-1", order: 0, nodes: [{ id: "text-1", type: "TEXT", content: { text: "Hola" }, style: { color: "#000" } }] }],
    });
    const app = new BuilderApp({ document });
    const module = registerInspectorModule(app);
    await app.start();
    module.service.select("text-1");
    module.service.update("content.text", "Bienvenido");
    assert.equal(module.service.read("content.text"), "Bienvenido");
    assert.equal(module.service.read("style.color"), "#000");
    assert.equal(app.isDirty, true);
    await app.destroy();
});

test("InspectorService conserva acordeones y scroll por nodo", async () => {
    const document = createDocument({
        canvases: [{ id: "canvas-1", order: 0, nodes: [
            { id: "node-1", type: "TEXT" },
            { id: "node-2", type: "IMAGE" },
        ] }],
    });
    const app = new BuilderApp({ document });
    const module = registerInspectorModule(app);
    await app.start();
    module.service.select("node-1");
    module.service.setGroupOpen("typography", false);
    module.service.setScroll(240);
    module.service.select("node-2");
    module.service.setScroll(80);
    module.service.select("node-1");
    assert.equal(module.service.isGroupOpen("typography"), false);
    assert.equal(module.service.getScroll(), 240);
    await app.destroy();
});

test("InspectorService encuentra y edita nodos anidados", async () => {
    const document = createDocument({
        canvases: [{ id: "canvas-1", order: 0, nodes: [{
            id: "card-1", type: "CARD", children: [{ id: "label-1", type: "TEXT", content: { text: "Días" } }],
        }] }],
    });
    const app = new BuilderApp({ document });
    const module = registerInspectorModule(app);
    await app.start();
    const selected = module.service.select("label-1");
    assert.equal(selected.parentId, "card-1");
    module.service.update("content.text", "Horas");
    assert.equal(module.service.read("content.text"), "Horas");
    await app.destroy();
});
