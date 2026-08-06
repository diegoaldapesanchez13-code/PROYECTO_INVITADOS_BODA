import assert from "node:assert/strict";
import test from "node:test";
import {
    applyCanvasesToR3Document,
    canvasesFromR3Document,
} from "../frontend/canvas/index.js";

test("R3 adapter conserva ids, orden, capas y altura", () => {
    const r3 = {
        id: "doc-r3",
        sections: [
            { id: "s2", type: "SECTION", name: "Segundo", order: 1, height: 900, children: [{ id: "text-1" }] },
            { id: "s1", type: "SECTION", name: "Primero", order: 0, height: 844, children: [] },
        ],
    };
    const canvases = canvasesFromR3Document(r3);
    assert.deepEqual(canvases.map((canvas) => canvas.id), ["s1", "s2"]);
    assert.equal(canvases[1].nodes[0].id, "text-1");
    const restored = applyCanvasesToR3Document(r3, canvases);
    assert.equal(restored.id, "doc-r3");
    assert.equal(restored.sections[1].height, 900);
    assert.equal(restored.sections[1].children[0].id, "text-1");
});
