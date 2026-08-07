import assert from "node:assert/strict";
import test from "node:test";

import {
    LayerStackService,
    LayerTreeState,
    LAYER_COMMANDS,
    executeLayerCommand,
} from "../frontend/layers/index.js";

function fixture() {
    return [
        {
            id: "background",
            name: "Fondo",
            type: "IMAGE",
            style: {
                zIndex: 90,
                responsive: {
                    mobile: { zIndex: 300, x: 50 },
                },
            },
            children: [],
        },
        {
            id: "card",
            name: "Card",
            type: "CARD",
            style: { zIndex: 2 },
            children: [
                {
                    id: "card-text",
                    name: "Texto Card",
                    type: "TEXT",
                    style: { zIndex: 20 },
                    children: [],
                },
            ],
        },
        {
            id: "title",
            name: "Título",
            type: "TEXT",
            style: { zIndex: 1 },
            children: [],
        },
    ];
}

test("normaliza el orden canónico y elimina zIndex responsive", () => {
    const service = new LayerStackService();
    const nodes = service.normalize(fixture());

    assert.deepEqual(nodes.map((node) => node.style.zIndex), [1, 2, 3]);
    assert.equal(nodes[0].style.responsive.mobile.zIndex, undefined);
    assert.equal(nodes[0].style.responsive.mobile.x, 50);
    assert.equal(nodes[1].children[0].style.zIndex, 1);
    assert.equal(service.validate(nodes).valid, true);
});

test("traer al frente modifica children y no solo el número", () => {
    const service = new LayerStackService();
    const result = service.bringToFront(service.normalize(fixture()), "background");

    assert.deepEqual(
        result.nodes.map((node) => node.id),
        ["card", "title", "background"],
    );
    assert.deepEqual(
        result.nodes.map((node) => node.style.zIndex),
        [1, 2, 3],
    );
});

test("subir y bajar trabajan entre hermanos", () => {
    const service = new LayerStackService();
    const normalized = service.normalize(fixture());

    const forward = service.bringForward(normalized, "background");
    assert.deepEqual(
        forward.nodes.map((node) => node.id),
        ["card", "background", "title"],
    );

    const backward = service.sendBackward(forward.nodes, "background");
    assert.deepEqual(
        backward.nodes.map((node) => node.id),
        ["background", "card", "title"],
    );
});

test("moveBefore y moveAfter exigen el mismo padre", () => {
    const service = new LayerStackService();
    const normalized = service.normalize(fixture());

    assert.throws(
        () => service.moveBefore(normalized, "card-text", "title"),
        /mismo contenedor/,
    );

    const result = service.moveBefore(normalized, "title", "card");
    assert.deepEqual(
        result.nodes.map((node) => node.id),
        ["background", "title", "card"],
    );
});

test("moveInside mueve una capa dentro de Card", () => {
    const service = new LayerStackService();
    const result = service.moveInside(
        service.normalize(fixture()),
        "title",
        "card",
    );

    assert.deepEqual(
        result.nodes.map((node) => node.id),
        ["background", "card"],
    );
    assert.deepEqual(
        result.nodes[1].children.map((node) => node.id),
        ["card-text", "title"],
    );
    assert.deepEqual(
        result.nodes[1].children.map((node) => node.style.zIndex),
        [1, 2],
    );
});

test("no permite ciclos ni contenedores inválidos", () => {
    const service = new LayerStackService();
    const normalized = service.normalize(fixture());

    assert.throws(
        () => service.moveInside(normalized, "card", "card-text"),
        /no acepta/,
    );
    assert.throws(
        () => service.moveInside(normalized, "card", "card"),
        /sí misma/,
    );
});

test("capas bloqueadas no pueden reordenarse", () => {
    const service = new LayerStackService();
    const nodes = service.normalize(fixture());
    nodes[0].locked = true;

    assert.throws(
        () => service.bringToFront(nodes, "background"),
        /bloqueada/,
    );
});

test("flatten devuelve árbol visual front-to-back", () => {
    const service = new LayerStackService();
    const nodes = service.normalize(fixture());
    const flat = service.flatten(nodes, {
        expanded: new Set(["card"]),
    });

    assert.deepEqual(
        flat.map((item) => item.id),
        ["title", "card", "card-text", "background"],
    );
    assert.equal(flat.find((item) => item.id === "card-text").depth, 1);
});

test("estado del árbol conserva selección expansión y drag", () => {
    const state = new LayerTreeState({
        expandedIds: ["card"],
    });

    state.select("title");
    state.beginDrag("title");
    state.updateDrag("card", "INSIDE");

    assert.equal(state.selectedId, "title");
    assert.equal(state.expandedIds.has("card"), true);
    assert.deepEqual(state.dragState, {
        nodeId: "title",
        targetId: "card",
        placement: "INSIDE",
    });

    assert.equal(state.endDrag().targetId, "card");
    assert.equal(state.dragState, null);
});

test("command dispatcher ejecuta comandos normalizados", () => {
    const service = new LayerStackService();
    const nodes = service.normalize(fixture());

    const result = executeLayerCommand(
        service,
        nodes,
        LAYER_COMMANDS.SEND_TO_BACK,
        { nodeId: "title" },
    );

    assert.deepEqual(
        result.nodes.map((node) => node.id),
        ["title", "background", "card"],
    );
});

test("duplicar regenera IDs de toda la rama", () => {
    const service = new LayerStackService();
    const nodes = service.normalize(fixture());
    let counter = 0;

    const result = service.duplicate(nodes, "card", {
        idFactory: () => `copy-${++counter}`,
    });

    assert.equal(result.duplicate.id, "copy-1");
    assert.equal(result.duplicate.children[0].id, "copy-2");
    assert.equal(
        new Set(result.nodes.map((node) => node.id)).size,
        result.nodes.length,
    );
});
