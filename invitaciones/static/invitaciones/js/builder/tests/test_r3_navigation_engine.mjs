import assert from "node:assert/strict";

import {
    NavigationEngine,
    NavigationResolver,
    ScrollService,
} from "../navigation/index.js";

const calls = [];
const target = {
    dataset: {
        r3SectionId: "section-rsvp",
    },
    scrollIntoView(options) {
        calls.push(options);
    },
};

const root = {
    querySelectorAll(selector) {
        assert.equal(
            selector,
            "[data-r3-section-id]"
        );

        return [
            {
                dataset: {
                    r3SectionId:
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
    resolver.resolve("section-rsvp"),
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

const result = engine.navigateToSection(
    "section-rsvp"
);

assert.equal(result.executed, true);
assert.equal(
    result.sectionId,
    "section-rsvp"
);
assert.deepEqual(calls, [
    {
        behavior: "smooth",
        block: "start",
        inline: "nearest",
    },
]);

const missing = engine.navigateToSection(
    "missing"
);

assert.equal(missing.executed, false);
assert.equal(
    missing.reason,
    "section-not-found"
);

console.log("OK navigation engine");
