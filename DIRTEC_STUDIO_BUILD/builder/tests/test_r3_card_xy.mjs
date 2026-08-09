import assert from "node:assert/strict";

function clamp(value, min, max) {
    return Math.min(
        Math.max(value, min),
        max
    );
}

function pointerToPercent({
    clientX,
    clientY,
    offsetX,
    offsetY,
    parentLeft,
    parentTop,
    parentWidth,
    parentHeight,
}) {
    const centerX =
        clientX - offsetX;

    const centerY =
        clientY - offsetY;

    return {
        x: clamp(
            (
                centerX
                - parentLeft
            ) / parentWidth * 100,
            -100,
            200
        ),
        y: clamp(
            (
                centerY
                - parentTop
            ) / parentHeight * 100,
            -100,
            200
        ),
    };
}

assert.deepEqual(
    pointerToPercent({
        clientX: 480,
        clientY: 550,
        offsetX: 0,
        offsetY: 0,
        parentLeft: 100,
        parentTop: 100,
        parentWidth: 760,
        parentHeight: 900,
    }),
    {
        x: 50,
        y: 50,
    }
);

assert.deepEqual(
    pointerToPercent({
        clientX: 556,
        clientY: 640,
        offsetX: 0,
        offsetY: 0,
        parentLeft: 100,
        parentTop: 100,
        parentWidth: 760,
        parentHeight: 900,
    }),
    {
        x: 60,
        y: 60,
    }
);

console.log(
    "R3.06.3 card XY tests: OK"
);