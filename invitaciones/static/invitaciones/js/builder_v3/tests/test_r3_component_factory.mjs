import assert from "node:assert/strict";

import {
    BuilderState,
    LAYOUT_MODES,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";

import {
    insertComponent,
    resolveInsertionTarget,
} from "../components/index.js";

const state = new BuilderState(createEmptyDocument());
const canvas = state.createNode(NODE_TYPES.SECTION, {
    name: "Portada",
    height: 900,
});

const text = insertComponent({
    state,
    type: NODE_TYPES.TEXT,
    selectedNodeId: canvas.id,
});

assert.equal(text.parentId, canvas.id);
assert.equal(text.sectionId, canvas.id);
assert.equal(text.layoutMode, LAYOUT_MODES.ABSOLUTE);
assert.equal(text.content.text, "Escribe aquí");
assert.equal(state.selection.nodeId, text.id);

const card = state.createNode(NODE_TYPES.CARD, {
    parentId: canvas.id,
    sectionId: canvas.id,
    layoutMode: LAYOUT_MODES.ABSOLUTE,
});

const button = insertComponent({
    state,
    type: NODE_TYPES.BUTTON,
    selectedNodeId: card.id,
});

assert.equal(button.parentId, card.id);
assert.equal(button.sectionId, canvas.id);
assert.equal(button.content.label, "Botón");
assert.equal(button.interaction.enabled, false);
assert.equal(resolveInsertionTarget(state, text.id).id, canvas.id);
assert.throws(
    () => insertComponent({ state, type: NODE_TYPES.MAP }),
    /no insertable/
);

console.log("✓ inserción de Texto y Botón en lienzos y cards");
