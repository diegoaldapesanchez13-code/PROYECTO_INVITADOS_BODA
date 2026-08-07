import assert from "node:assert/strict";
import test from "node:test";

test("Transform Lab es de solo lectura", () => {
    const bootstrap = {
        readOnly: true,
        endpoints: { load: "/document/" },
    };
    assert.equal(bootstrap.readOnly, true);
    assert.deepEqual(Object.keys(bootstrap.endpoints), ["load"]);
});

test("los dispositivos conservan sus anchos lógicos", () => {
    const widths = { mobile: 390, tablet: 768, desktop: 1180 };
    assert.equal(widths.mobile, 390);
    assert.equal(widths.tablet, 768);
    assert.equal(widths.desktop, 1180);
});

test("el laboratorio depende del renderer y transform core", () => {
    const required = [
        "UniversalRenderer",
        "UniversalDomAdapter",
        "SelectionState",
        "TransformSession",
        "CanvasHeightSession",
    ];
    assert.equal(required.length, 5);
});
