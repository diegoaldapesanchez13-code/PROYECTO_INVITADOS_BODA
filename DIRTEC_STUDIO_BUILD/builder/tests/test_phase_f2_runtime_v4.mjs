import assert from "node:assert/strict";
import test from "node:test";
import {
    canonicalizeDocumentV4,
} from "../core/runtime_v4.js";

function v3() {
    return {
        schemaVersion: 3,
        page: { id: "page", name: "Test", type: "PAGE", settings: {} },
        sections: [{
            id: "c1", type: "SECTION", name: "Portada",
            parentId: null, sectionId: "c1", order: 0,
            visible: true, locked: false, coordinateSpace: "SECTION",
            x: 50, y: 50, width: 100, height: 844,
            style: {}, content: {}, responsive: {}, children: [],
        }],
        nodes: [{
            id: "t1", type: "TEXT", parentId: "c1", sectionId: "c1",
            order: 0, visible: true, locked: false,
            coordinateSpace: "SECTION", x: 50, y: 50, width: 50,
            height: 20, style: {}, content: { text: "Hola" },
            responsive: {}, children: [],
        }],
        assets: [],
        responsive: {
            baseDevice: "desktop",
            inheritance: { tablet: "desktop", mobile: "tablet" },
        },
        meta: {},
    };
}

test("V3 becomes canonical mobile-first V4", () => {
    const d = canonicalizeDocumentV4(v3());
    assert.equal(d.schemaVersion, 4);
    assert.equal(d.canvases[0].type, "CANVAS");
    assert.equal(d.nodes[0].canvasId, "c1");
    assert.equal(d.responsive.baseDevice, "mobile");
    assert.equal("sections" in d, false);
});

