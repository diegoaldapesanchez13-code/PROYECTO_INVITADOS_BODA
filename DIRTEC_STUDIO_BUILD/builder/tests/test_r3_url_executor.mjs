import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createNode,
} from "../core/index.js";

import {
    BrowserInteractionRuntime,
    INTERACTION_TYPES,
    InteractionEngine,
    validateWebUrl,
} from "../interaction/index.js";

function urlNode(value, openInNewTab = false) {
    return createNode(
        NODE_TYPES.IMAGE,
        {
            interaction: {
                enabled: true,
                action: {
                    type:
                        INTERACTION_TYPES.URL,
                    value,
                    openInNewTab,
                },
            },
        }
    );
}

const calls = [];
const runtime = {
    openUrl(url, options) {
        calls.push({ url, options });
        return {
            executed: true,
            reason: null,
            url,
            openInNewTab:
                options.openInNewTab,
        };
    },
};

const engine = new InteractionEngine({
    runtime,
});

const executed = engine.execute(
    urlNode(
        "https://dirtec.mx/contacto",
        true
    )
);

assert.equal(executed.handled, true);
assert.equal(executed.status, "executed");
assert.equal(executed.intent, "OPEN_URL");
assert.equal(
    executed.payload.url,
    "https://dirtec.mx/contacto"
);
assert.equal(
    executed.payload.openInNewTab,
    true
);
assert.equal(calls.length, 1);
assert.equal(
    calls[0].options.openInNewTab,
    true
);

for (const unsafe of [
    "javascript:alert(1)",
    "data:text/html,test",
    "file:///tmp/test",
    "",
    "no es url",
]) {
    const result = engine.execute(
        urlNode(unsafe)
    );

    assert.equal(result.handled, false);
    assert.equal(result.status, "invalid");
}

assert.equal(calls.length, 1);
assert.equal(
    validateWebUrl("https://example.com").valid,
    true
);
assert.equal(
    validateWebUrl("javascript:alert(1)").valid,
    false
);

const assigned = [];
const fakeWindow = {
    location: {
        assign(value) {
            assigned.push(value);
        },
    },
    open() {
        return { opener: {} };
    },
};

const browserRuntime =
    new BrowserInteractionRuntime({
        windowRef: fakeWindow,
    });

assert.equal(
    browserRuntime.openUrl(
        "https://example.com"
    ).executed,
    true
);
assert.deepEqual(
    assigned,
    ["https://example.com"]
);

console.log("OK URL executor validates and navigates");
