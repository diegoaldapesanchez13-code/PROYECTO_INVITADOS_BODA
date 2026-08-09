import assert from "node:assert/strict";

import {
    BuilderState,
    LAYOUT_MODES,
    NODE_TYPES,
    createEmptyDocument,
    migrateLegacyConfig,
    validateDocument,
} from "../core/index.js";

const state = new BuilderState(
    createEmptyDocument()
);

const section = state.createNode(
    NODE_TYPES.CANVAS,
    {
        name: "Cuenta regresiva",
    }
);

const background = state.createNode(
    NODE_TYPES.BACKGROUND,
    {
        parentId: section.id,
        canvasId: section.id,
    }
);

const card = state.createNode(
    NODE_TYPES.CARD,
    {
        parentId: section.id,
        canvasId: section.id,
        layoutMode: LAYOUT_MODES.FLOW,
    }
);

const countdown = state.createNode(
    NODE_TYPES.COUNTDOWN,
    {
        parentId: card.id,
        canvasId: section.id,
        x: 50,
        y: 60,
    }
);

assert.equal(
    state.getChildren(section.id).length,
    2
);

state.updateNode(countdown.id, {
    x: 55,
    y: 65,
});

assert.equal(
    state.getNode(countdown.id).x,
    55
);

const duplicate = state.duplicateNode(
    card.id
);

assert.ok(duplicate.id !== card.id);
assert.equal(
    state.getChildren(section.id).length,
    3
);

state.moveNode(
    countdown.id,
    duplicate.id,
    0
);

assert.equal(
    state.getNode(countdown.id).parentId,
    duplicate.id
);

state.reorderNode(
    duplicate.id,
    0
);

assert.equal(
    state.getChildren(section.id)[0].id,
    duplicate.id
);

const serialized = state.serialize();
const parsed = JSON.parse(serialized);
const validation = validateDocument(parsed);

assert.equal(validation.valid, true);

assert.equal(state.undo(), true);
assert.equal(state.redo(), true);

const migrated = migrateLegacyConfig(
    {
        sections: [
            {
                id: 1,
                type: "CUENTA_REGRESIVA",
                title: "Cuenta regresiva",
                visible: true,
                order: 0,
                config: {
                    layoutAutoHeight: true,
                    layoutPaddingX: 20,
                    layoutPaddingY: 24,
                    counterX: 50,
                    counterY: 68,
                    counterWidth: 92,
                    counterScale: 1,
                },
            },
        ],
    },
    {
        components: [
            {
                id: 7,
                canvasId: 1,
                tipo: "TEXTO",
                x: 50,
                y: 20,
                width: 60,
                height: 10,
                properties: {
                    text: "Faltan",
                },
            },
        ],
    }
);

assert.equal(
    migrated.schemaVersion,
    4
);
assert.equal(
    migrated.canvases.length,
    1
);
assert.ok(
    migrated.nodes.some(
        (node) =>
            node.type === NODE_TYPES.COUNTDOWN
    )
);
assert.ok(
    migrated.nodes.some(
        (node) =>
            node.type === NODE_TYPES.TEXT
    )
);

console.log("R3.01 tests: OK");