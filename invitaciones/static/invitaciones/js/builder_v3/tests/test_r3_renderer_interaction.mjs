import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createEmptyDocument,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
} from "../interaction/index.js";

import {
    UniversalRenderer,
} from "../renderer/renderer.js";

const node = createNode(
    NODE_TYPES.IMAGE,
    {
        interaction: {
            enabled: true,
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

const calls = [];
const results = [];

const engine = {
    execute(receivedNode, options) {
        calls.push({
            receivedNode,
            options,
        });

        return {
            handled: true,
            status: "ready",
            intent: "OPEN_URL",
            nodeId: receivedNode.id,
        };
    },
};

const renderer = new UniversalRenderer({
    editable: false,
    device: "mobile",
    interactionEngine: engine,
    onInteractionResult(result, context) {
        results.push({ result, context });
    },
});

renderer.document = createEmptyDocument();

const event = {
    prevented: false,
    stopped: false,
    preventDefault() {
        this.prevented = true;
    },
    stopPropagation() {
        this.stopped = true;
    },
};

const listeners = new Map();
const element = {
    dataset: {},
    addEventListener(type, listener) {
        listeners.set(type, listener);
    },
};

renderer.bindNodeEvents(element, node);

assert.equal(
    element.dataset.r3Interactive,
    "1"
);
assert.equal(
    typeof listeners.get("click"),
    "function"
);

listeners.get("click")(event);

assert.equal(event.prevented, true);
assert.equal(event.stopped, true);
assert.equal(calls.length, 1);
assert.equal(
    calls[0].receivedNode.id,
    node.id
);
assert.equal(
    calls[0].options.trigger,
    "CLICK"
);
assert.equal(
    calls[0].options.metadata.device,
    "mobile"
);
assert.equal(
    calls[0].options.metadata.editable,
    false
);
assert.equal(results.length, 1);
assert.equal(
    results[0].result.intent,
    "OPEN_URL"
);

const editableCalls = [];
const editableRenderer =
    new UniversalRenderer({
        editable: true,
        interactionEngine: engine,
        onNodeClick(receivedNode) {
            editableCalls.push(
                receivedNode.id
            );
        },
    });

const editableListeners = new Map();
const editableElement = {
    dataset: {},
    addEventListener(type, listener) {
        editableListeners.set(
            type,
            listener
        );
    },
};

editableRenderer.bindNodeEvents(
    editableElement,
    node
);
editableListeners.get("click")({
    stopPropagation() {},
});

assert.deepEqual(
    editableCalls,
    [node.id]
);
assert.equal(calls.length, 1);
assert.equal(
    editableElement.dataset
        .r3Interactive,
    undefined
);

const disabledNode = createNode(
    NODE_TYPES.TEXT
);
const disabledListeners = new Map();

renderer.bindNodeEvents(
    {
        dataset: {},
        addEventListener(type, listener) {
            disabledListeners.set(
                type,
                listener
            );
        },
    },
    disabledNode
);

assert.equal(
    disabledListeners.has("click"),
    false
);

const errors = [];
const failingRenderer =
    new UniversalRenderer({
        editable: false,
        interactionEngine: {
            execute() {
                throw new Error(
                    "fallo controlado"
                );
            },
        },
        onInteractionError(error) {
            errors.push(error.message);
        },
    });

const failure =
    failingRenderer.executeInteraction(
        node
    );

assert.equal(
    failure.status,
    "error"
);
assert.equal(
    failure.reason,
    "interaction-error"
);
assert.deepEqual(
    errors,
    ["fallo controlado"]
);

console.log(
    "OK renderer delegates interaction"
);
