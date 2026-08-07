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
    NODE_TYPES.SECTION,
    {
        name: "RSVP",
        order: 0,
    }
);
destination.sectionId = destination.id;
document.sections.push(destination);

const calls = [];
const runtime = {
    navigateSection(sectionId, options) {
        calls.push({ sectionId, options });

        return {
            executed: true,
            reason: null,
            sectionId,
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
                type: INTERACTION_TYPES.SECTION,
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
    "NAVIGATE_SECTION"
);
assert.equal(
    result.payload.sectionId,
    destination.id
);
assert.equal(calls.length, 1);
assert.equal(
    calls[0].sectionId,
    destination.id
);
assert.equal(
    calls[0].options.behavior,
    "smooth"
);

const renamed = structuredClone(document);
renamed.sections[0].name = "Confirmación";

const renamedResult = engine.execute(
    node,
    { document: renamed }
);
assert.equal(
    renamedResult.status,
    "executed"
);

const reordered = structuredClone(document);
reordered.sections[0].order = 99;

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
    NODE_TYPES.SECTION,
    {
        id: "another-section",
        name: "Otro lienzo",
    }
);
otherSection.sectionId = otherSection.id;
deleted.sections.push(otherSection);

const deletedResult = engine.execute(
    node,
    { document: deleted }
);
assert.equal(deletedResult.handled, false);
assert.equal(deletedResult.status, "invalid");
assert.equal(
    deletedResult.reason,
    "section-not-found"
);

console.log("OK section executor");
