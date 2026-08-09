import assert from "node:assert/strict";
import test from "node:test";

import { BuilderState } from "../core/state.js";
import {
    migrateDocumentToV4,
} from "../core/schema_v4.js";

test("V3 remaps SECTION aliases before BuilderState validation", () => {
    const document = migrateDocumentToV4(
        legacySectionAliasFixture()
    );

    assert.equal(document.canvases[0].id, "canvas-portada");
    assert.equal(document.canvases[1].id, "canvas-detalles");
    assert.equal(document.nodes[0].parentId, "canvas-portada");
    assert.equal(document.nodes[0].canvasId, "canvas-portada");
    assert.equal(
        find(document, "text-1").parentId,
        "card-1"
    );
    assert.equal(
        find(document, "image-1").interaction.action.value,
        "canvas-detalles"
    );
    assert.equal(
        find(document, "image-1").interaction.action.target,
        "canvas-detalles"
    );

    assertDocumentGraph(document);

    const state = new BuilderState(document);
    assert.equal(state.validate().valid, true);
});

function legacySectionAliasFixture() {
    return {
        schemaVersion: 3,
        page: {
            id: "page-legacy",
            name: "Boda legacy",
            type: "PAGE",
            settings: {},
        },
        sections: [
            legacySection(
                "canvas-portada",
                "section-portada",
                [
                    "background-1",
                    "decoration-1",
                    "card-1",
                    "map-1",
                    "video-1",
                    "rsvp-1",
                ]
            ),
            legacySection(
                "canvas-detalles",
                "section-detalles",
                []
            ),
        ],
        nodes: [
            legacyNode("background-1", "BACKGROUND", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 100,
                height: 100,
            }),
            legacyNode("decoration-1", "DECORATION", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 30,
                height: 20,
                x: 20,
                y: 10,
            }),
            legacyNode("card-1", "CARD", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 84,
                height: 45,
                children: [
                    "text-1",
                    "image-1",
                    "button-1",
                ],
            }),
            legacyNode("text-1", "TEXT", {
                parentId: "card-1",
                sectionId: "section-portada",
                canvasId: "section-portada",
                width: 70,
                height: 12,
                content: {
                    text: "Fernanda & Diego",
                },
            }),
            legacyNode("image-1", "IMAGE", {
                parentId: "card-1",
                sectionId: "section-portada",
                canvasId: "section-portada",
                width: 40,
                height: 22,
                interaction: {
                    enabled: true,
                    action: {
                        type: "CANVAS",
                        value: "section-detalles",
                        target: "section-detalles",
                    },
                },
            }),
            legacyNode("button-1", "BUTTON", {
                parentId: "card-1",
                sectionId: "section-portada",
                canvasId: "section-portada",
                width: 34,
                height: 9,
            }),
            legacyNode("map-1", "MAP", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 84,
                height: 24,
                y: 78,
            }),
            legacyNode("video-1", "VIDEO", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 84,
                height: 28,
                y: 64,
            }),
            legacyNode("rsvp-1", "RSVP", {
                parentId: "section-portada",
                sectionId: "section-portada",
                coordinateSpace: "SECTION",
                width: 84,
                height: 30,
                y: 90,
            }),
        ],
        assets: [
            {
                id: "asset-bg",
                url: "/media/bg.jpg",
            },
        ],
        responsive: {
            baseDevice: "desktop",
            inheritance: {
                tablet: "desktop",
                mobile: "tablet",
            },
        },
        meta: {
            source: "legacy-section-aliases",
        },
    };
}

function legacySection(id, sectionId, children) {
    return {
        id,
        sectionId,
        type: "SECTION",
        name: id,
        parentId: null,
        order: 0,
        coordinateSpace: "SECTION",
        x: 50,
        y: 50,
        width: 100,
        height: 900,
        children,
    };
}

function legacyNode(id, type, overrides = {}) {
    return {
        id,
        type,
        name: id,
        parentId: null,
        sectionId: null,
        order: 0,
        visible: true,
        locked: false,
        layoutMode: "ABSOLUTE",
        coordinateSpace: "PARENT",
        x: 50,
        y: 50,
        width: 50,
        height: 10,
        style: {},
        content: {},
        responsive: {},
        children: [],
        ...overrides,
    };
}

function find(document, id) {
    return document.nodes.find((item) => item.id === id);
}

function assertDocumentGraph(document) {
    const allNodes = [
        ...document.canvases,
        ...document.nodes,
    ];
    const ids = new Set(allNodes.map((item) => item.id));
    const canvasIds = new Set(
        document.canvases.map((item) => item.id)
    );

    for (const item of allNodes) {
        if (item.parentId) {
            assert.ok(
                ids.has(item.parentId),
                `${item.id} parent exists`
            );
        }

        if (item.type !== "CANVAS" && item.canvasId) {
            assert.ok(
                canvasIds.has(item.canvasId),
                `${item.id} canvas exists`
            );
        }

        for (const childId of item.children || []) {
            assert.ok(
                ids.has(childId),
                `${item.id} child ${childId} exists`
            );
        }
    }
}
