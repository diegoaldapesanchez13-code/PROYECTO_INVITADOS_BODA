import assert from "node:assert/strict";
import { BuilderState } from "../core/state.js";
import { createEmptyDocument, NODE_TYPES } from "../core/schema.js";
import { insertComponent } from "../components/factory.js";

const state = new BuilderState(createEmptyDocument());
const section = state.createNode(NODE_TYPES.CANVAS, { name: "Lienzo", height: 900 });
const countdown = insertComponent({ state, type: NODE_TYPES.COUNTDOWN, selectedNodeId: section.id });
const units = state.getChildren(countdown.id);
assert.equal(units.length, 4);
assert.ok(units.every((node) => node.type === NODE_TYPES.CARD));
for (const unit of units) {
    const children = state.getChildren(unit.id);
    assert.equal(children.length, 2);
    assert.ok(children.every((node) => node.type === NODE_TYPES.TEXT));
    assert.deepEqual(children.map((node) => node.content.binding.role).sort(), ["label", "value"]);
}
console.log("test_r3_composite_countdown: ok");
