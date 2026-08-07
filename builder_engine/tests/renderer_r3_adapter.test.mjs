import assert from "node:assert/strict";
import test from "node:test";
import { RendererRegistry, registerR3Renderers } from "../frontend/renderer/index.js";

test("adaptador R3 traduce editable según el modo universal", () => {
    const registry = new RendererRegistry();
    let received = null;
    registerR3Renderers(registry, {
        VIDEO(node, context) {
            received = context;
            return { id: node.id, type: node.type, tag: "video", children: [] };
        },
    });
    const renderer = registry.resolve("VIDEO");
    const result = renderer.render(
        { id: "video-1", type: "VIDEO" },
        { mode: "PREVIEW", document: {}, canvas: {} },
        [],
    );
    assert.equal(result.tag, "video");
    assert.equal(received.editable, false);
    assert.equal(received.mode, "preview");
});
