import assert from "node:assert/strict";

import {
    compareBackToFront,
    compareFrontToBack,
} from "../layers/layer_stack.js";

const nodes = [
    {
        id: "back",
        zIndex: 1,
        order: 0,
    },
    {
        id: "middle",
        zIndex: 2,
        order: 1,
    },
    {
        id: "front",
        zIndex: 3,
        order: 2,
    },
];

assert.deepEqual(
    [...nodes]
        .sort(compareFrontToBack)
        .map((node) => node.id),
    [
        "front",
        "middle",
        "back",
    ]
);

assert.deepEqual(
    [...nodes]
        .sort(compareBackToFront)
        .map((node) => node.id),
    [
        "back",
        "middle",
        "front",
    ]
);

console.log(
    "R3.07.4 Layer Levels tests: OK"
);