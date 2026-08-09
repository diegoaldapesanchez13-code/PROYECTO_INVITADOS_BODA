import assert from "node:assert/strict";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";
import { insertComponent } from "../components/index.js";
import { countdownPanel } from "../inspector/panels/countdown.js";

const state = new BuilderState(createEmptyDocument());
const canvas = state.createNode(NODE_TYPES.CANVAS, { height: 900 });
const countdown = insertComponent({ state, type: NODE_TYPES.COUNTDOWN, selectedNodeId: canvas.id });

const units = state.getChildren(countdown.id);
assert.equal(units.length, 4);
assert.ok(units.every((unit) => unit.type === NODE_TYPES.CARD));

const daysChildren = state.getChildren(units[0].id);
const value = daysChildren.find((node) => node.content.binding?.role === "value");
const label = daysChildren.find((node) => node.content.binding?.role === "label");
assert.equal(value.style.fontFamily, "'Playfair Display', serif");
assert.equal(label.style.fontFamily, "Montserrat, sans-serif");
assert.notEqual(value.style.fontFamily, label.style.fontFamily);
assert.equal(value.content.binding.unit, "days");

const fields = countdownPanel()
    .flatMap((panel) => panel.fields || [])
    .map((field) => field.path);
assert.ok(fields.includes("content.targetDate"));
assert.ok(fields.includes("content.values.0"));

console.log("✓ countdown compuesto por cards y textos editables");
