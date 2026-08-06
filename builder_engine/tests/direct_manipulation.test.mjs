import assert from "node:assert/strict";
import test from "node:test";
import {
    pixelsToPercent,
    dragTransform,
    resizeTransform,
    rotationFromPoints,
    resolveResponsiveStyle,
    writeResponsiveStyle,
} from "../frontend/workspace/transform_math.js";

test("convierte pixeles a porcentaje", () => {
    assert.equal(pixelsToPercent(39, 390), 10);
});

test("calcula drag sobre el canvas", () => {
    const result = dragTransform(
        { x: 50, y: 50 },
        { x: 39, y: -70 },
        { width: 390, height: 700 },
    );
    assert.equal(result.x, 60);
    assert.equal(result.y, 40);
});

test("resize desde el sureste modifica ancho y centro", () => {
    const result = resizeTransform(
        { x: 50, width: 40 },
        { x: 39, y: 0 },
        { width: 390, height: 700 },
        "se",
    );
    assert.equal(result.width, 50);
    assert.equal(result.x, 55);
});

test("rotación usa el ángulo entre puntos", () => {
    const rotation = rotationFromPoints(
        { x: 0, y: 0 },
        { x: 10, y: 0 },
        { x: 0, y: 10 },
        0,
    );
    assert.equal(Math.round(rotation), 90);
});

test("guarda transform por dispositivo sin destruir base", () => {
    const style = { x: 50, y: 50, responsive: { mobile: { x: 45 } } };
    const next = writeResponsiveStyle(style, { x: 60, width: 80 }, "tablet");
    assert.equal(next.x, 50);
    assert.equal(next.responsive.mobile.x, 45);
    assert.equal(next.responsive.tablet.x, 60);
    assert.equal(next.responsive.tablet.width, 80);
});

test("resuelve override responsive", () => {
    const style = {
        x: 50,
        y: 50,
        width: 70,
        responsive: { desktop: { x: 30, width: 40 } },
    };
    const resolved = resolveResponsiveStyle(style, "desktop");
    assert.equal(resolved.x, 30);
    assert.equal(resolved.y, 50);
    assert.equal(resolved.width, 40);
    assert.equal(resolved.responsive, undefined);
});
