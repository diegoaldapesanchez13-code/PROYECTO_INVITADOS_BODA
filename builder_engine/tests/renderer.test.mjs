import assert from "node:assert/strict";
import test from "node:test";
import { BuilderApp } from "../frontend/app/index.js";
import { createDocument } from "../frontend/document/index.js";
import {
    RENDER_MODES,
    RendererRegistry,
    registerRendererModule,
} from "../frontend/renderer/index.js";

test("RendererModule se registra y produce un árbol headless", async () => {
    const app = new BuilderApp({ document: createDocument({
        canvases: [{ id: "canvas-1", order: 0, width: 390, height: 844, nodes: [
            { id: "text-1", type: "TEXT", content: { text: "Hola" } },
        ] }],
    }) });
    const module = registerRendererModule(app);
    await app.start();
    const result = module.service.render();
    assert.equal(result.mode, "EDIT");
    assert.equal(result.canvases[0].children[0].content, "Hola");
    assert.equal(result.metadata.editable, true);
    await app.destroy();
});

test("Renderer usa el mismo árbol en EDIT, PREVIEW y PUBLIC con capacidades distintas", async () => {
    const app = new BuilderApp({ document: createDocument({
        canvases: [{ id: "c", nodes: [{ id: "b", type: "BUTTON", content: { text: "Abrir" } }] }],
    }) });
    const module = registerRendererModule(app);
    await app.start();
    const edit = module.service.render({ mode: RENDER_MODES.EDIT });
    const preview = module.service.render({ mode: RENDER_MODES.PREVIEW });
    const publicResult = module.service.render({ mode: RENDER_MODES.PUBLIC });
    assert.equal(edit.canvases[0].children[0].attributes.disabled, true);
    assert.equal(preview.canvases[0].children[0].attributes.disabled, false);
    assert.equal(publicResult.metadata.interactive, true);
    await app.destroy();
});

test("RendererRegistry permite extensiones por tipo", async () => {
    const registry = new RendererRegistry();
    registry.register("BADGE", (node, context) => ({
        id: node.id,
        type: node.type,
        tag: "span",
        attributes: { "data-mode": context.mode },
        content: node.content?.text,
        children: [],
    }));
    registry.registerFallback((node) => ({ id: node.id, type: node.type, tag: "div", children: [] }));
    const app = new BuilderApp({ document: createDocument({
        canvases: [{ id: "c", nodes: [{ id: "badge", type: "BADGE", content: { text: "Nuevo" } }] }],
    }) });
    const module = registerRendererModule(app, { registry, defaultRenderers: false });
    await app.start();
    const result = module.service.render({ mode: "PUBLIC" });
    assert.equal(result.canvases[0].children[0].tag, "span");
    assert.equal(result.canvases[0].children[0].attributes["data-mode"], "PUBLIC");
    await app.destroy();
});

test("Renderer omite nodos invisibles y conserva jerarquía anidada", async () => {
    const app = new BuilderApp({ document: createDocument({
        canvases: [{ id: "c", nodes: [{
            id: "card", type: "CARD", children: [
                { id: "visible", type: "TEXT", content: { text: "Sí" } },
                { id: "hidden", type: "TEXT", visible: false, content: { text: "No" } },
            ],
        }] }],
    }) });
    const module = registerRendererModule(app);
    await app.start();
    const result = module.service.render();
    assert.equal(result.canvases[0].children[0].children.length, 1);
    assert.equal(result.canvases[0].children[0].children[0].id, "visible");
    await app.destroy();
});
