import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
    BuilderState,
    LAYOUT_MODES,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";

const state = new BuilderState(createEmptyDocument());
const canvas = state.createNode(NODE_TYPES.CANVAS, {
    layoutMode: LAYOUT_MODES.ABSOLUTE,
    coordinateSpace: "PARENT",
    x: 10,
    y: 20,
    width: 42,
    height: 900,
    rotation: 30,
    scale: 2,
});

assert.equal(canvas.layoutMode, LAYOUT_MODES.FLOW);
assert.equal(canvas.coordinateSpace, "CANVAS");
assert.equal(canvas.x, 50);
assert.equal(canvas.y, 50);
assert.equal(canvas.width, 100);
assert.equal(canvas.height, 900);
assert.equal(canvas.rotation, 0);
assert.equal(canvas.scale, 1);

const updated = state.updateNode(canvas.id, {
    layoutMode: LAYOUT_MODES.LAYER,
    width: 75,
    height: 1200,
    x: 1,
});

assert.equal(updated.layoutMode, LAYOUT_MODES.FLOW);
assert.equal(updated.width, 100);
assert.equal(updated.height, 1200);
assert.equal(updated.x, 50);

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const canvasPanel = fs.readFileSync(
    path.join(root, "inspector/panels/canvas.js"),
    "utf8",
);
const inspector = fs.readFileSync(
    path.join(root, "inspector/index.js"),
    "utf8",
);

assert.match(canvasPanel, /key:\s*"height"/);
assert.match(canvasPanel, /key:\s*"name"/);
assert.match(canvasPanel, /id:\s*"duplicate"/);
assert.match(canvasPanel, /id:\s*"delete"/);
assert.doesNotMatch(canvasPanel, /key:\s*"overflow"/);
assert.doesNotMatch(canvasPanel, /key:\s*"layoutMode"/);
assert.doesNotMatch(canvasPanel, /key:\s*"zIndex"/);
assert.doesNotMatch(canvasPanel, /key:\s*"x"/);
assert.doesNotMatch(canvasPanel, /key:\s*"width"/);
assert.doesNotMatch(canvasPanel, /key:\s*"opacity"/);
assert.match(inspector, /node\.type\s*===\s*NODE_TYPES\.CANVAS/);
assert.match(inspector, /return canvasPanel\(\)/);
assert.doesNotMatch(inspector, /createElement\(\s*"canvas"\s*\)/);
assert.match(inspector, /createElement\(\s*"section"\s*\)/);

console.log("Canvas contract test: OK");
