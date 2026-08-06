import assert from "node:assert/strict";

import {
    NODE_TYPES,
} from "../core/index.js";

import {
    getInsertableComponent,
    listInsertableComponents,
} from "../components/index.js";

const items = listInsertableComponents();
assert.deepEqual(
    items.map((item) => item.type),
    [
        NODE_TYPES.TEXT,
        NODE_TYPES.BUTTON,
        NODE_TYPES.CARD,
        NODE_TYPES.CONTAINER,
        NODE_TYPES.COUNTDOWN,
        NODE_TYPES.SEPARATOR,
        NODE_TYPES.ICON,
    ]
);
assert.equal(getInsertableComponent("text").type, NODE_TYPES.TEXT);
assert.equal(getInsertableComponent(NODE_TYPES.BUTTON).label, "Botón");
assert.equal(getInsertableComponent("card").type, NODE_TYPES.CARD);
assert.equal(getInsertableComponent("countdown").label, "Cuenta regresiva");
assert.equal(getInsertableComponent("unknown"), null);

items[0].label = "Mutado";
assert.equal(getInsertableComponent("text").label, "Texto");

console.log("✓ catálogo completo de componentes base");
