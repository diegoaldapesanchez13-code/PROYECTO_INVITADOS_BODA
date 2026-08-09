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

const second = state.createNode(NODE_TYPES.CANVAS, {
    name: "Segundo lienzo",
});

state.selectNode(second.id);
const secondNode = useAsset({
    state,
    asset: {
        id: "image-1",
        type: ASSET_TYPES.IMAGE,
        name: "Foto",
        url: "https://example.com/foto.jpg",
    },
});
assert.equal(secondNode.parentId, second.id);
assert.equal(secondNode.canvasId, second.id);

const card = state.createNode(NODE_TYPES.CARD, {
    name: "Card destino",
    parentId: second.id,
    canvasId: second.id,
});
const child = state.createNode(NODE_TYPES.TEXT, {
    name: "Texto hijo",
    parentId: card.id,
    canvasId: second.id,
});

state.selectNode(child.id);
const nested = useAsset({
    state,
    asset: {
        id: "decor-1",
        type: ASSET_TYPES.DECORATION,
        name: "Decoracion",
        url: "https://example.com/decor.png",
    },
});
assert.equal(nested.parentId, card.id);
assert.equal(nested.canvasId, second.id);
console.log("✓ video asset crea una capa VIDEO");
