import assert from "node:assert/strict";
import test from "node:test";
import { CanvasWorkspaceController } from "../frontend/workspace/index.js";

function fakeApp(canvases) {
    let documentValue = { canvases: structuredClone(canvases) };
    return {
        getDocument() {
            return structuredClone(documentValue);
        },
        updateDocument(mutator) {
            const draft = structuredClone(documentValue);
            mutator(draft);
            documentValue = draft;
        },
    };
}

function fakeWorkspace() {
    let value = { selectedCanvasId: null };
    return {
        get value() { return structuredClone(value); },
        update(mutator) {
            const draft = structuredClone(value);
            mutator(draft);
            value = draft;
        },
    };
}

const base = [
    { id: "a", name: "Portada", order: 10, visible: true, nodes: [] },
    { id: "b", name: "Detalles", order: 20, visible: true, nodes: [] },
];

test("inicializa seleccionando el primer lienzo", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp(base),
        workspace: fakeWorkspace(),
    }).initialize();

    assert.equal(controller.selectedCanvasId, "a");
});

test("crea y selecciona un lienzo", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp(base),
        workspace: fakeWorkspace(),
    }).initialize();

    const created = controller.create({ name: "RSVP" });
    assert.equal(controller.list().length, 3);
    assert.equal(controller.selectedCanvasId, created.id);
    assert.equal(created.name, "RSVP");
});

test("duplica regenerando ID", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp(base),
        workspace: fakeWorkspace(),
    }).initialize();

    const duplicated = controller.duplicate("a");
    assert.notEqual(duplicated.id, "a");
    assert.equal(duplicated.name, "Portada copia");
});

test("reordena lienzos", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp(base),
        workspace: fakeWorkspace(),
    }).initialize();

    assert.equal(controller.move("b", "up"), true);
    assert.deepEqual(controller.list().map((item) => item.id), ["b", "a"]);
});

test("impide eliminar el último lienzo", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp([{ id: "a", name: "Único", order: 10, nodes: [] }]),
        workspace: fakeWorkspace(),
    }).initialize();

    assert.throws(() => controller.remove("a"), /al menos un lienzo/);
});

test("renombra el lienzo", () => {
    const controller = new CanvasWorkspaceController({
        app: fakeApp(base),
        workspace: fakeWorkspace(),
    }).initialize();

    controller.rename("a", "Nueva portada");
    assert.equal(controller.list()[0].name, "Nueva portada");
});
