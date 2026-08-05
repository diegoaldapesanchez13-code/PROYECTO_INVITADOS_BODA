import assert from "node:assert/strict";

import {
    LAYOUT_MODES,
    NODE_TYPES,
} from "../core/index.js";

import {
    TRANSFORM_KINDS,
    effectiveLayoutMode,
    getTransformPolicy,
} from "../canvas/transform_policy.js";

const section = {
    type: NODE_TYPES.SECTION,
    layoutMode: LAYOUT_MODES.ABSOLUTE,
    locked: false,
};

assert.equal(
    effectiveLayoutMode(section),
    LAYOUT_MODES.FLOW
);

assert.equal(
    getTransformPolicy(section).kind,
    TRANSFORM_KINDS.NONE
);

const background = {
    type: NODE_TYPES.BACKGROUND,
    layoutMode: LAYOUT_MODES.LAYER,
    locked: false,
};

assert.equal(
    effectiveLayoutMode(background),
    LAYOUT_MODES.LAYER
);

assert.equal(
    getTransformPolicy(background).kind,
    TRANSFORM_KINDS.BACKGROUND_PAN
);

const card = {
    type: NODE_TYPES.CARD,
    layoutMode: LAYOUT_MODES.ABSOLUTE,
    locked: false,
};

assert.equal(
    getTransformPolicy(card).kind,
    TRANSFORM_KINDS.GEOMETRY
);

assert.equal(
    getTransformPolicy(card).resizable,
    true
);

console.log(
    "R3.06.2 transform policy tests: OK"
);