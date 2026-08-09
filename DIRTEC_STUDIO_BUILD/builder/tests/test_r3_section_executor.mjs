import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createEmptyDocument,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
    InteractionEngine,
} from "../interaction/index.js";

const document = createEmptyDocument();
const destination = createNode(
    NODE_TYPES.CANVAS,
    {
        name: "RSVP",
        order: 0,
    }
);
destination.canvasId = destination.id;
document.canvases.push(destination);

const calls = [];
const runtime = {
    navigateCanvas(canvasId, options) {
        calls.push({ canvasId, options });

        return {
            executed: true,
            reason: null,
            canvasId,
        };
    },
};

const engine = new InteractionEngine({
    runtime,
});

const node = createNode(
    NODE_TYPES.BUTTON,
    {
        interaction: {
            enabled: true,
            action: {
                type: INTERACTION_TYPES.CANVAS,
                value: destination.id,
            },
        },
    }
);

const result = engine.execute(node, {
    document,
});

assert.equal(result.handled, true);
assert.equal(result.status, "executed");
assert.equal(
    result.intent,
    "NAVIGATE_CANVAS"
);
assert.equal(
    result.payload.canvasId,
    destination.id
);
assert.equal(calls.length, 1);
assert.equal(
    calls[0].canvasId,
    destination.id
);
assert.equal(
    calls[0].options.behavior,
    "smooth"
);

const renamed = structuredClone(document);
renamed.canvases[0].name = "Confirmación";

const renamedResult = engine.execute(
    node,
    { document: renamed }
);
assert.equal(
    renamedResult.status,
    "executed"
);

const reordered = structuredClone(document);
reordered.canvases[0].order = 99;

const reorderedResult = engine.execute(
    node,
    { document: reordered }
);
assert.equal(
    reorderedResult.status,
    "executed"
);

const deleted = createEmptyDocument();
const otherSection = createNode(
    NODE_TYPES.CANVAS,
    {
        id: "another-section",
        name: "Otro lienzo",
    }
);
otherSection.canvasId = otherSection.id;
deleted.canvases.push(otherSection);

const deletedResult = engine.execute(
    node,
    { document: deleted }
);
assert.equal(deletedResult.handled, false);
assert.equal(deletedResult.status, "invalid");
assert.equal(
    deletedResult.reason,
    "canvas-not-found"
);

console.log("OK canvas executor");
