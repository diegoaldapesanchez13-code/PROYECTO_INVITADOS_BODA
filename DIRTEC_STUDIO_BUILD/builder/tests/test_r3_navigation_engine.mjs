import assert from "node:assert/strict";

import {
    NavigationEngine,
    NavigationResolver,
    ScrollService,
} from "../navigation/index.js";

const calls = [];
const target = {
    dataset: {
        r3CanvasId: "canvas-rsvp",
    },
    scrollIntoView(options) {
        calls.push(options);
    },
};

const root = {
    querySelectorAll(selector) {
        assert.equal(
            selector,
            "[data-r3-canvas-id]"
        );

        return [
            {
                dataset: {
                    r3CanvasId:
                        "section-cover",
                },
            },
            target,
        ];
    },
};

const resolver = new NavigationResolver({
    root,
});

assert.equal(
    resolver.resolve("canvas-rsvp"),
    target
);
assert.equal(
    resolver.resolve("missing"),
    null
);

const engine = new NavigationEngine({
    resolver,
    scrollService: new ScrollService(),
});

const result = engine.navigateToCanvas(
    "canvas-rsvp"
);

assert.equal(result.executed, true);
assert.equal(
    result.canvasId,
    "canvas-rsvp"
);
assert.deepEqual(calls, [
    {
        behavior: "smooth",
        block: "start",
        inline: "nearest",
    },
]);

const missing = engine.navigateToCanvas(
    "missing"
);

assert.equal(missing.executed, false);
assert.equal(
    missing.reason,
    "canvas-not-found"
);

console.log("OK navigation engine");
