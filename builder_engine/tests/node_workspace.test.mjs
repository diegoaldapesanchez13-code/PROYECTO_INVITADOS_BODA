import assert from "node:assert/strict";
import test from "node:test";
import { NodeWorkspaceController } from "../frontend/workspace/node_workspace_controller.js";

function fakeApp() {
    let documentValue = {
        canvases: [{
            id: "canvas-1",
            nodes: [{
                id: "container-1",
                type: "CONTAINER",
                name: "Contenedor",
                visible: true,
                locked: false,
                children: [{
                    id: "text-1",
                    type: "TEXT",
                    name: "Título",
                    visible: true,
                    locked: false,
                    content: { text: "Hola" },
                    style: { x: 50 },
                    children: [],
                }],
            }],
        }],
    };
    return {
        getDocument() { return structuredClone(documentValue); },
        updateDocument(mutator) {
            const draft = structuredClone(documentValue);
            mutator(draft);
            documentValue = draft;
        },
    };
}

function fakeWorkspace() {
    let value = { selectedNodeId: null };
    return {
        get value() { return structuredClone(value); },
        update(mutator) {
            const draft = structuredClone(value);
            mutator(draft);
            value = draft;
        },
    };
}

function fakeCanvasController() {
    return {
        selectedCanvasId: "canvas-1",
        getSelected() {
            return fakeApp().getDocument().canvases[0];
        },
    };
}

test("selecciona nodos anidados", () => {
    const app = fakeApp();
    const canvasController = {
        selectedCanvasId: "canvas-1",
        getSelected() { return app.getDocument().canvases[0]; },
    };
    const controller = new NodeWorkspaceController({
        app,
        workspace: fakeWorkspace(),
        canvasController,
    }).initialize();

    const selected = controller.select("text-1");
    assert.equal(selected.name, "Título");
});

test("edita texto y posición", () => {
    const app = fakeApp();
    const canvasController = {
        selectedCanvasId: "canvas-1",
        getSelected() { return app.getDocument().canvases[0]; },
    };
    const controller = new NodeWorkspaceController({
        app,
        workspace: fakeWorkspace(),
        canvasController,
    });
    controller.select("text-1");
    controller.update("content.text", "Nuevo texto");
    controller.update("style.x", 25);

    assert.equal(controller.getSelected().content.text, "Nuevo texto");
    assert.equal(controller.getSelected().style.x, 25);
});

test("cambia visibilidad y bloqueo", () => {
    const app = fakeApp();
    const canvasController = {
        selectedCanvasId: "canvas-1",
        getSelected() { return app.getDocument().canvases[0]; },
    };
    const controller = new NodeWorkspaceController({
        app,
        workspace: fakeWorkspace(),
        canvasController,
    });
    controller.select("text-1");
    controller.toggleVisibility();
    controller.toggleLock();

    assert.equal(controller.getSelected().visible, false);
    assert.equal(controller.getSelected().locked, true);
});

test("elimina un nodo anidado", () => {
    const app = fakeApp();
    const canvasController = {
        selectedCanvasId: "canvas-1",
        getSelected() { return app.getDocument().canvases[0]; },
    };
    const controller = new NodeWorkspaceController({
        app,
        workspace: fakeWorkspace(),
        canvasController,
    });
    controller.select("text-1");
    controller.remove();

    assert.equal(app.getDocument().canvases[0].nodes[0].children.length, 0);
    assert.equal(controller.selectedNodeId, null);
});
