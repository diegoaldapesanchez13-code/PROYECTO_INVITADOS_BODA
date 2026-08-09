import assert from "node:assert/strict";
import test from "node:test";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
    validateDocument,
} from "../core/index.js";

import {
    ASSET_TYPES,
} from "../assets/asset_manager.js";

import {
    useAsset,
} from "../assets/asset_nodes.js";

import {
    insertComponent,
} from "../components/index.js";

function imageAsset(id = "image-1") {
    return {
        id,
        type: ASSET_TYPES.IMAGE,
        name: "Imagen",
        url: `https://example.com/${id}.jpg`,
    };
}

function decorationAsset(id = "decor-1") {
    return {
        id,
        type: ASSET_TYPES.DECORATION,
        name: "Decoracion",
        url: `https://example.com/${id}.png`,
    };
}

test("F.4 insertion uses selected canvas and selected containers", () => {
    const state = new BuilderState(createEmptyDocument());
    const canvasA = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas A" });
    const canvasB = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas B" });

    state.selectNode(canvasA.id);
    const textA = insertComponent({ state, type: NODE_TYPES.TEXT });
    assert.equal(textA.parentId, canvasA.id);
    assert.equal(textA.canvasId, canvasA.id);

    state.selectNode(canvasB.id);
    const textB = insertComponent({ state, type: NODE_TYPES.TEXT });
    assert.equal(textB.parentId, canvasB.id);
    assert.equal(textB.canvasId, canvasB.id);

    const cardB = insertComponent({
        state,
        type: NODE_TYPES.CARD,
        selectedNodeId: canvasB.id,
    });
    const childImage = useAsset({
        state,
        asset: imageAsset("image-card"),
        selectedNodeId: cardB.id,
    });
    assert.equal(childImage.parentId, cardB.id);
    assert.equal(childImage.canvasId, canvasB.id);

    state.selectNode(childImage.id);
    const nestedButton = insertComponent({
        state,
        type: NODE_TYPES.BUTTON,
    });
    assert.equal(nestedButton.parentId, cardB.id);
    assert.equal(nestedButton.canvasId, canvasB.id);
});

test("F.4 non-container selection falls back to its real canvas", () => {
    const state = new BuilderState(createEmptyDocument());
    const canvasA = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas A" });
    const canvasB = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas B" });
    const imageB = useAsset({
        state,
        asset: imageAsset("image-b"),
        selectedNodeId: canvasB.id,
    });

    state.selectNode(imageB.id);
    const separator = insertComponent({
        state,
        type: NODE_TYPES.SEPARATOR,
    });
    assert.equal(separator.parentId, canvasB.id);
    assert.equal(separator.canvasId, canvasB.id);

    const decoration = useAsset({
        state,
        asset: decorationAsset("decor-b"),
    });
    assert.equal(decoration.parentId, canvasB.id);
    assert.equal(decoration.canvasId, canvasB.id);

    assert.notEqual(separator.parentId, canvasA.id);
    assert.notEqual(decoration.parentId, canvasA.id);
});

test("F.4 duplication, move and serialization preserve hierarchy", () => {
    const state = new BuilderState(createEmptyDocument());
    const canvasA = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas A" });
    const canvasB = state.createNode(NODE_TYPES.CANVAS, { name: "Canvas B" });
    const card = insertComponent({
        state,
        type: NODE_TYPES.CARD,
        selectedNodeId: canvasB.id,
    });
    const text = insertComponent({
        state,
        type: NODE_TYPES.TEXT,
        selectedNodeId: card.id,
    });

    const duplicate = state.duplicateNode(card.id);
    assert.notEqual(duplicate.id, card.id);
    assert.equal(duplicate.parentId, canvasB.id);
    assert.equal(duplicate.canvasId, canvasB.id);
    assert.equal(duplicate.children.length, 1);
    assert.notEqual(duplicate.children[0], text.id);
    assert.equal(state.getNode(duplicate.children[0]).canvasId, canvasB.id);

    const duplicatedCanvas = state.duplicateNode(canvasB.id);
    assert.notEqual(duplicatedCanvas.id, canvasB.id);
    for (const childId of duplicatedCanvas.children) {
        const child = state.getNode(childId);
        assert.equal(child.parentId, duplicatedCanvas.id);
        assert.equal(child.canvasId, duplicatedCanvas.id);
    }

    state.moveNode(card.id, canvasA.id);
    assert.equal(state.getNode(card.id).parentId, canvasA.id);
    assert.equal(state.getNode(card.id).canvasId, canvasA.id);
    assert.equal(state.getNode(text.id).canvasId, canvasA.id);

    assert.throws(
        () => state.moveNode(card.id, text.id),
        /descendiente/,
    );

    const coerced = state.createNode(NODE_TYPES.TEXT, {
        parentId: canvasA.id,
        canvasId: canvasB.id,
    });
    assert.equal(coerced.canvasId, canvasA.id);

    const reloaded = new BuilderState(JSON.parse(state.serialize()));
    const validation = validateDocument(reloaded.document);
    assert.equal(validation.valid, true);
    assert.equal(reloaded.getNode(card.id).parentId, canvasA.id);
    assert.equal(reloaded.getNode(text.id).canvasId, canvasA.id);
});
