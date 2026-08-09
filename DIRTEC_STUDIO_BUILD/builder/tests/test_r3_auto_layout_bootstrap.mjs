import assert from "node:assert/strict";

import {
    AutoLayoutEngine,
} from "../layout/auto_layout.js";

const engine = new AutoLayoutEngine({
    state: {
        document: {
            nodes: [],
        },
        transaction(_label, callback) {
            return callback();
        },
    },
    renderer: {
        update() {},
    },
});

assert.doesNotThrow(() => {
    assert.equal(engine.applyAll(), false);
});

console.log("AutoLayoutEngine bootstrap test: OK");
