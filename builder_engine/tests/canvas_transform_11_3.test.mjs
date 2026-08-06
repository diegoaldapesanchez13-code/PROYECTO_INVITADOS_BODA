
import assert from "node:assert/strict";
import test from "node:test";
import { SelectionState } from "../frontend/selection/selection_state.js";
import { TransformSession, TRANSFORM_HANDLES } from "../frontend/transform/transform_session.js";
import { CanvasHeightSession } from "../frontend/transform/canvas_height_session.js";
import { screenDeltaToLogical } from "../frontend/transform/coordinate_mapper.js";
import { createSelectionOverlay } from "../frontend/transform/selection_overlay_contract.js";

test("selección primaria y múltiple son deterministas", () => {
    const state = new SelectionState();
    state.select("a");
    state.select("b", { additive: true });
    assert.deepEqual(state.selectedIds, ["a", "b"]);
    assert.equal(state.primaryId, "b");
    state.toggle("b");
    assert.deepEqual(state.selectedIds, ["a"]);
    assert.equal(state.primaryId, "a");
});

test("existen exactamente ocho handles de resize", () => {
    assert.deepEqual(TRANSFORM_HANDLES, ["n","ne","e","se","s","sw","w","nw"]);
});

test("MOVE respeta zoom", () => {
    const session = new TransformSession({
        nodeId: "n1",
        transform: { x: 10, y: 20, width: 100, height: 50 },
        pointer: { x: 0, y: 0 },
        zoom: 2,
    });
    const value = session.update({ x: 40, y: 20 });
    assert.equal(value.x, 30);
    assert.equal(value.y, 30);
});

test("resize SE modifica ancho y alto reales", () => {
    const session = new TransformSession({
        nodeId: "n1",
        transform: { x: 10, y: 20, width: 100, height: 50 },
        pointer: { x: 0, y: 0 },
        operation: "RESIZE",
        handle: "se",
    });
    const value = session.update({ x: 25, y: 15 });
    assert.equal(value.width, 125);
    assert.equal(value.height, 65);
    assert.equal(value.x, 10);
    assert.equal(value.y, 20);
});

test("resize NW conserva borde opuesto", () => {
    const session = new TransformSession({
        nodeId: "n1",
        transform: { x: 10, y: 20, width: 100, height: 50 },
        pointer: { x: 0, y: 0 },
        operation: "RESIZE",
        handle: "nw",
    });
    const value = session.update({ x: 20, y: 10 });
    assert.equal(value.x, 30);
    assert.equal(value.y, 30);
    assert.equal(value.width, 80);
    assert.equal(value.height, 40);
});

test("cancel revierte y commit genera transacción", () => {
    const session = new TransformSession({
        nodeId: "n1",
        transform: { x: 5, y: 5, width: 20, height: 20 },
        pointer: { x: 0, y: 0 },
    });
    session.update({ x: 10, y: 10 });
    assert.equal(session.cancel().x, 5);

    const committed = new TransformSession({
        nodeId: "n2",
        transform: { x: 0, y: 0, width: 10, height: 10 },
        pointer: { x: 0, y: 0 },
    });
    committed.update({ x: 5, y: 6 });
    const tx = committed.commit();
    assert.equal(tx.before.x, 0);
    assert.equal(tx.after.x, 5);
    assert.equal(tx.after.y, 6);
});

test("altura de canvas respeta zoom y límites", () => {
    const session = new CanvasHeightSession({
        height: 1000, pointerY: 100, zoom: 2, minHeight: 500, maxHeight: 1100,
    });
    assert.equal(session.update(300), 1100);
    assert.equal(session.update(-200), 850);
});

test("mapper evita que zoom desincronice frame y contenido", () => {
    assert.deepEqual(
        screenDeltaToLogical({ dx: 80, dy: 40 }, { zoom: 2, scale: .5 }),
        { dx: 80, dy: 40 },
    );
    assert.deepEqual(
        screenDeltaToLogical({ dx: 80, dy: 40 }, { zoom: 2, scale: 1 }),
        { dx: 40, dy: 20 },
    );
});

test("overlay usa ocho handles y rotación para nodo editable", () => {
    const overlay = createSelectionOverlay({
        id: "image-1",
        layout: { transform: { x: 10, y: 20, width: 30, height: 40 } },
    });
    assert.equal(overlay.handles.length, 8);
    assert.equal(overlay.rotationHandle.operation, "ROTATE");
    assert.equal(overlay.frame.width, 30);
});

test("nodo bloqueado no expone transformaciones", () => {
    const overlay = createSelectionOverlay({ id: "locked", locked: true });
    assert.equal(overlay.handles.length, 0);
    assert.equal(overlay.rotationHandle, null);
    assert.equal(overlay.moveEnabled, false);
});
