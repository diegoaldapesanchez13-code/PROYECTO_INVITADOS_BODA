import assert from "node:assert/strict";
import { BuilderState, NODE_TYPES, createEmptyDocument } from "../core/index.js";
import { useAsset } from "../assets/asset_nodes.js";
import { ASSET_TYPES } from "../assets/asset_manager.js";

const state = new BuilderState(createEmptyDocument());
const section = state.createNode(NODE_TYPES.CANVAS, { name: "Lienzo" });
const node = useAsset({
    state,
    selectedNodeId: section.id,
    asset: {
        id: "video-1",
        type: ASSET_TYPES.VIDEO,
        name: "Mi video",
        url: "blob:https://example.com/video-1",
        metadata: { width: 1920, height: 1080 },
    },
});

assert.equal(node.type, NODE_TYPES.VIDEO);
assert.equal(node.content.sourceType, "library");
assert.equal(node.content.assetId, "video-1");
assert.equal(node.content.source, "blob:https://example.com/video-1");
assert.equal(node.parentId, section.id);
console.log("✓ video asset crea una capa VIDEO");
