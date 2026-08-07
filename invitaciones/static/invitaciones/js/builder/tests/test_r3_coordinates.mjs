import assert from "node:assert/strict";

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function move({
    x,
    y,
    deltaX,
    deltaY,
    parentWidth,
    parentHeight,
}) {
    return {
        x: clamp(
            x + deltaX / Math.max(parentWidth, 1) * 100,
            -100,
            200
        ),
        y: clamp(
            y + deltaY / Math.max(parentHeight, 1) * 100,
            -100,
            200
        ),
    };
}

assert.deepEqual(
    move({
        x: 50,
        y: 50,
        deltaX: 76,
        deltaY: 90,
        parentWidth: 760,
        parentHeight: 900,
    }),
    {
        x: 60,
        y: 60,
    }
);

assert.equal(
    move({
        x: 50,
        y: 50,
        deltaX: 0,
        deltaY: 5000,
        parentWidth: 760,
        parentHeight: 1,
    }).y,
    200
);

console.log(
    "R3.06.1 coordinate tests: OK"
);