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

const text = insertComponent({ state, type: NODE_TYPES.TEXT, selectedNodeId: canvas.id });
assert.equal(text.parentId, canvas.id);
assert.equal(text.sectionId, canvas.id);
assert.equal(text.layoutMode, LAYOUT_MODES.ABSOLUTE);
assert.equal(text.content.text, "Escribe aquí");

const card = insertComponent({ state, type: NODE_TYPES.CARD, selectedNodeId: canvas.id });
assert.equal(card.parentId, canvas.id);
assert.equal(card.style.backgroundColor, "#ffffff");

const button = insertComponent({ state, type: NODE_TYPES.BUTTON, selectedNodeId: card.id });
assert.equal(button.parentId, card.id);
assert.equal(button.sectionId, canvas.id);
assert.equal(button.content.label, "Botón");
assert.equal(button.interaction.enabled, false);

const container = insertComponent({ state, type: NODE_TYPES.CONTAINER, selectedNodeId: canvas.id });
assert.equal(container.style.backgroundColor, "transparent");

const countdown = insertComponent({ state, type: NODE_TYPES.COUNTDOWN, selectedNodeId: container.id });
assert.equal(countdown.parentId, container.id);
assert.deepEqual(countdown.content.labels, ["Días", "Horas", "Minutos", "Segundos"]);
assert.equal(countdown.style.valueFontFamily, "Georgia, serif");
assert.equal(countdown.style.labelColor, "#777971");
assert.equal(countdown.style.itemBorderRadius, 16);

const separator = insertComponent({ state, type: NODE_TYPES.SEPARATOR, selectedNodeId: card.id });
assert.equal(separator.style.orientation, "horizontal");

const icon = insertComponent({ state, type: NODE_TYPES.ICON, selectedNodeId: card.id });
assert.equal(icon.content.value, "✦");

assert.equal(resolveInsertionTarget(state, text.id).id, canvas.id);
assert.throws(
    () => insertComponent({ state, type: NODE_TYPES.MAP }),
    /no insertable/
);

console.log("✓ inserción de componentes base y anidamiento");
