import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createEmptyDocument,
    createNode,
    normalizeDocument,
    serializeDocument,
} from "../core/index.js";

import {
    INTERACTION_TRIGGERS,
    INTERACTION_TYPES,
    createDefaultInteraction,
    normalizeInteraction,
} from "../interaction/index.js";

const defaults = createDefaultInteraction();

assert.deepEqual(defaults, {
    enabled: false,
    trigger: INTERACTION_TRIGGERS.CLICK,
    action: {
        type: INTERACTION_TYPES.NONE,
        value: "",
        target: "",
        openInNewTab: false,
    },
});

const image = createNode(NODE_TYPES.IMAGE);
assert.deepEqual(image.interaction, defaults);

const configured = createNode(
    NODE_TYPES.TEXT,
    {
        interaction: {
            enabled: true,
            trigger: INTERACTION_TRIGGERS.CLICK,
            action: {
                type: INTERACTION_TYPES.URL,
                value: "https://dirtec.mx",
                openInNewTab: true,
            },
        },
    }
);

assert.equal(configured.interaction.enabled, true);
assert.equal(
    configured.interaction.action.type,
    INTERACTION_TYPES.URL
);
assert.equal(
    configured.interaction.action.value,
    "https://dirtec.mx"
);
assert.equal(
    configured.interaction.action.openInNewTab,
    true
);

const legacyDocument = createEmptyDocument();
legacyDocument.nodes.push({
    ...createNode(NODE_TYPES.IMAGE),
    interaction: undefined,
});

const normalized = normalizeDocument(
    legacyDocument
);

assert.deepEqual(
    normalized.nodes[0].interaction,
    defaults,
    "Los documentos anteriores reciben interaction por defecto"
);

normalized.nodes[0].interaction = normalizeInteraction({
    enabled: true,
    action: {
        type: INTERACTION_TYPES.WHATSAPP,
        value: "5214771234567",
    },
});

const restored = JSON.parse(
    serializeDocument(normalized)
);

assert.equal(
    restored.nodes[0].interaction.action.type,
    INTERACTION_TYPES.WHATSAPP
);
assert.equal(
    restored.nodes[0].interaction.action.value,
    "5214771234567"
);

const invalid = normalizeInteraction({
    enabled: 1,
    trigger: "UNKNOWN",
    action: {
        type: "UNKNOWN",
        value: 123,
        target: null,
        openInNewTab: 1,
    },
});

assert.equal(
    invalid.trigger,
    INTERACTION_TRIGGERS.CLICK
);
assert.equal(
    invalid.action.type,
    INTERACTION_TYPES.NONE
);
assert.equal(invalid.action.value, "123");
assert.equal(invalid.action.target, "");
assert.equal(invalid.action.openInNewTab, true);

console.log("OK interaction model and persistence");
