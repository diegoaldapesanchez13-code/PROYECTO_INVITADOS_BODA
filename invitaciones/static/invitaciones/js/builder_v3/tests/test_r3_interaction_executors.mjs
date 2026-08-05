import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
    InteractionEngine,
} from "../interaction/index.js";

const engine = new InteractionEngine();

function nodeFor(type, values = {}) {
    return createNode(
        NODE_TYPES.BUTTON,
        {
            interaction: {
                enabled: true,
                action: {
                    type,
                    value:
                        values.value || "",
                    target:
                        values.target || "",
                    openInNewTab:
                        values.openInNewTab
                        ?? false,
                },
            },
        }
    );
}

const cases = [
    [
        INTERACTION_TYPES.NONE,
        null,
        false,
    ],
    [
        INTERACTION_TYPES.URL,
        "OPEN_URL",
        true,
    ],
    [
        INTERACTION_TYPES.GOOGLE_MAPS,
        "OPEN_GOOGLE_MAPS",
        true,
    ],
    [
        INTERACTION_TYPES.WHATSAPP,
        "OPEN_WHATSAPP",
        true,
    ],
    [
        INTERACTION_TYPES.SECTION,
        "NAVIGATE_SECTION",
        true,
    ],
];

for (const [type, intent, handled] of cases) {
    const result = engine.execute(
        nodeFor(type, {
            value:
                type === INTERACTION_TYPES.URL
                    ? "https://example.com"
                    : "valor",
            target: "destino",
        })
    );

    assert.equal(result.handled, handled);
    assert.equal(result.intent, intent);
}

console.log("OK interaction executors produce intents");
