import assert from "node:assert/strict";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";

import {
    DEFAULT_CANVAS_HEIGHT,
    MOBILE_CANVAS_WIDTH,
    createBlankCanvasConfig,
} from "../canvas/canvas_manager.js";

const state = new BuilderState(createEmptyDocument());

const first = state.createNode(
    NODE_TYPES.SECTION,
    createBlankCanvasConfig({ name: "Portada" }),
);

const child = state.createNode(NODE_TYPES.TEXT, {
    name: "Título",
    parentId: first.id,
    sectionId: first.id,
    content: { text: "Hola" },
});

const second = state.createNode(
    NODE_TYPES.SECTION,
    createBlankCanvasConfig({
        name: "Detalles",
        height: 1200,
    }),
);

assert.equal(MOBILE_CANVAS_WIDTH, 390);
assert.equal(first.height, DEFAULT_CANVAS_HEIGHT);
assert.equal(second.height, 1200);
assert.equal(state.document.sections.length, 2);

const clone = state.duplicateNode(first.id);
assert.equal(state.document.sections.length, 3);
assert.equal(state.getChildren(clone.id).length, 1);
assert.notEqual(state.getChildren(clone.id)[0].id, child.id);
assert.equal(state.getChildren(clone.id)[0].sectionId, clone.id);

state.reorderNode(second.id, 0);
assert.equal(
    [...state.document.sections].sort((a, b) => a.order - b.order)[0].id,
    second.id,
);

const deletedIds = state.deleteNode(clone.id);
assert.ok(deletedIds.includes(clone.id));
assert.equal(state.document.sections.length, 2);
assert.equal(
    state.document.nodes.some((node) => node.sectionId === clone.id),
    false,
);

console.log("✓ múltiples lienzos móviles, duplicación, orden y borrado");
