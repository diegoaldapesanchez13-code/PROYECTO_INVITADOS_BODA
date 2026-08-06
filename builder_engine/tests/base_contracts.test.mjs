import assert from "node:assert/strict";
import test from "node:test";

import {
    createTransformContract,
    resolveTransform,
    writeTransformOverride,
} from "../frontend/layout/index.js";
import {
    createCanvasSizeContract,
    resolveCanvasSize,
    writeCanvasHeight,
} from "../frontend/canvas/canvas_size_contract.js";
import { LayerStackService } from "../frontend/layers/index.js";
import {
    createNodeInteractionContract,
    nodeIsActionable,
} from "../frontend/interaction/node_interaction_contract.js";
import { CanvasViewportState } from "../frontend/viewport/index.js";
import { migrateDocumentToBaseContracts } from "../frontend/migration/schema_1_contract_migrator.js";

test("mobile es base y responsive no admite zIndex", () => {
    const contract = createTransformContract({
        transform: { x: 50, y: 50, width: 70, height: 30 },
        responsive: {
            tablet: { x: 40, zIndex: 200 },
        },
    });

    assert.equal(resolveTransform(contract, "mobile").x, 50);
    assert.equal(resolveTransform(contract, "tablet").x, 40);
    assert.equal(contract.responsive.tablet.zIndex, undefined);
});

test("escribe override de tamaño por dispositivo", () => {
    const contract = writeTransformOverride(
        createTransformContract(),
        { width: 80, height: 40 },
        "desktop",
    );

    assert.equal(resolveTransform(contract, "desktop").width, 80);
    assert.equal(resolveTransform(contract, "mobile").width, 50);
});

test("canvas conserva ancho fijo y altura editable", () => {
    const size = createCanvasSizeContract({
        responsive: { mobile: { height: 1200 } },
    });

    assert.equal(resolveCanvasSize(size, "mobile").width, 390);
    assert.equal(resolveCanvasSize(size, "mobile").height, 1200);
    assert.equal(resolveCanvasSize(size, "tablet").width, 768);
    assert.equal(resolveCanvasSize(size, "tablet").height, 1200);
});

test("altura tablet puede sobrescribirse sin cambiar mobile", () => {
    const base = createCanvasSizeContract({
        responsive: { mobile: { height: 1100 } },
    });
    const next = writeCanvasHeight(base, "tablet", 900);

    assert.equal(resolveCanvasSize(next, "mobile").height, 1100);
    assert.equal(resolveCanvasSize(next, "tablet").height, 900);
});

test("LayerStack normaliza por hermanos", () => {
    const service = new LayerStackService();
    const nodes = service.normalize([
        { id: "a", style: { zIndex: 99 }, children: [] },
        { id: "b", style: { zIndex: 1 }, children: [
            { id: "c", style: { zIndex: 50 }, children: [] },
        ] },
    ]);

    assert.equal(nodes[0].style.zIndex, 1);
    assert.equal(nodes[1].style.zIndex, 2);
    assert.equal(nodes[1].children[0].style.zIndex, 1);
});

test("frente y fondo reorganizan el arreglo", () => {
    const service = new LayerStackService();
    const nodes = [
        { id: "a", children: [] },
        { id: "b", children: [] },
        { id: "c", children: [] },
    ];

    assert.deepEqual(
        service.bringToFront(nodes, "a").map((node) => node.id),
        ["b", "c", "a"],
    );
    assert.deepEqual(
        service.sendToBack(nodes, "c").map((node) => node.id),
        ["c", "a", "b"],
    );
});

test("imagen puede ser botón mediante interacción universal", () => {
    const interaction = createNodeInteractionContract({
        ariaLabel: "Abrir ubicación",
        interactions: [{
            trigger: "CLICK",
            action: {
                type: "GOOGLE_MAPS",
                value: "https://maps.google.com/",
                openInNewTab: true,
            },
        }],
        states: {
            pressed: { scale: 0.97 },
        },
    });

    const node = { type: "IMAGE", interaction };
    assert.equal(nodeIsActionable(node), true);
    assert.equal(interaction.states.pressed.scale, 0.97);
});

test("viewport separa edit y preview continuo", () => {
    const viewport = new CanvasViewportState();
    assert.equal(viewport.value.mode, "EDIT");
    viewport.setMode("PREVIEW_CONTINUOUS");
    viewport.setZoom(1.5);
    viewport.setDevice("tablet");

    assert.equal(viewport.value.mode, "PREVIEW_CONTINUOUS");
    assert.equal(viewport.value.zoom, 1.5);
    assert.equal(viewport.value.device, "tablet");
});

test("migrador agrega contratos sin eliminar datos existentes", () => {
    const source = {
        globals: {},
        canvases: [{
            id: "canvas-1",
            height: 1000,
            style: { overflow: "hidden" },
            nodes: [{
                id: "image-1",
                type: "IMAGE",
                content: { alt: "Mapa" },
                style: {
                    x: 50,
                    y: 40,
                    width: 80,
                    height: 30,
                    zIndex: 15,
                    responsive: {
                        mobile: { x: 45, zIndex: 99 },
                    },
                },
                interactions: [{
                    trigger: "CLICK",
                    action: { type: "URL", value: "https://example.com" },
                }],
                children: [],
            }],
        }],
    };

    const migrated = migrateDocumentToBaseContracts(source);
    const canvas = migrated.canvases[0];
    const node = canvas.nodes[0];

    assert.equal(resolveCanvasSize(canvas.size, "mobile").height, 1000);
    assert.equal(node.layout.transform.width, 80);
    assert.equal(node.layout.responsive.mobile.zIndex, undefined);
    assert.equal(node.style.zIndex, 1);
    assert.equal(nodeIsActionable(node), true);
});
