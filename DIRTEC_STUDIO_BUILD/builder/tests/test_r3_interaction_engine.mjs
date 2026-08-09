import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TRIGGERS,
    INTERACTION_TYPES,
    InteractionEngine,
} from "../interaction/index.js";

const engine = new InteractionEngine();

const disabled = createNode(
    NODE_TYPES.IMAGE
);

assert.deepEqual(
    engine.execute(disabled),
    {
        handled: false,
        status: "skipped",
        reason: "interaction-disabled",
        interactionType: null,
        trigger: null,
        nodeId: null,
    }
);

const urlNode = createNode(
    NODE_TYPES.IMAGE,
    {
        interaction: {
            enabled: true,
            trigger:
                INTERACTION_TRIGGERS.CLICK,
            action: {
                type:
                    INTERACTION_TYPES.URL,
                value:
                    "https://dirtec.mx",
                openInNewTab: true,
            },
        },
    }
);

const urlResult = engine.execute(
    urlNode
);

assert.equal(urlResult.handled, true);
assert.equal(urlResult.status, "ready");
assert.equal(urlResult.intent, "OPEN_URL");
assert.equal(
    urlResult.payload.url,
    "https://dirtec.mx"
);
assert.equal(
    urlResult.payload.openInNewTab,
    true
);
assert.equal(
    urlResult.interactionType,
    INTERACTION_TYPES.URL
);
assert.equal(urlResult.nodeId, urlNode.id);

const mismatch = engine.execute(
    urlNode,
    {
        trigger: "LONG_PRESS",
    }
);

assert.equal(mismatch.handled, false);
assert.equal(
    mismatch.reason,
    "trigger-mismatch"
);

const sectionNode = createNode(
    NODE_TYPES.TEXT,
    {
        interaction: {
            enabled: true,
            action: {
                type:
                    INTERACTION_TYPES.CANVAS,
                target: "section-destino",
            },
        },
    }
);

const sectionResult =
    engine.execute(sectionNode);

assert.equal(
    sectionResult.intent,
    "NAVIGATE_CANVAS"
);
assert.equal(
    sectionResult.payload.canvasId,
    "section-destino"
);

const customEngine =
    new InteractionEngine({
        executors: {
            [INTERACTION_TYPES.NONE]:
                () => ({
                    handled: false,
                    status: "custom",
                }),
        },
    });

assert.equal(
    customEngine.hasExecutor(
        INTERACTION_TYPES.NONE
    ),
    true
);
assert.equal(
    customEngine.hasExecutor(
        INTERACTION_TYPES.URL
    ),
    false
);

customEngine.registerExecutor(
    INTERACTION_TYPES.URL,
    (context) => ({
        handled: true,
        status: "custom",
        received:
            context.action.value,
    })
);

assert.equal(
    customEngine.execute(urlNode).received,
    "https://dirtec.mx"
);

assert.throws(
    () => new InteractionEngine({
        executors: null,
    }),
    /executors debe ser Map u objeto/
);

console.log("OK interaction engine routing");
