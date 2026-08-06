import assert from "node:assert/strict";
import test from "node:test";
import {
    isLegacyMigrationPending,
    migrateLegacyDocument,
} from "../frontend/migration/index.js";

function documentWithLegacy() {
    return {
        schemaVersion: 1,
        documentVersion: 1,
        builderVersion: "0.14.0",
        metadata: { eventId: 1, name: "Evento" },
        theme: {},
        assets: [],
        globals: {
            legacyMigrationPending: true,
            legacyEditorConfig: {
                theme: { primary: "#2f7a4d" },
                layout: { maxWidth: 430 },
                sections: [
                    {
                        id: "section-1",
                        sectionId: 1,
                        type: "PORTADA",
                        title: "Fernanda & Diego",
                        description: "Nuestra boda",
                        visible: true,
                        order: 10,
                        config: {
                            sectionHeight: 780,
                            backgroundAsset: {
                                id: 15,
                                url: "/media/portada.jpg",
                                title: "Portada",
                                isVideo: false,
                            },
                            customLayers: [
                                {
                                    id: "layer-1",
                                    kind: "text",
                                    name: "Fecha",
                                    text: "20 · 12 · 2026",
                                    x: 50,
                                    y: 75,
                                },
                            ],
                        },
                    },
                    {
                        id: "section-2",
                        sectionId: 2,
                        type: "CUENTA_REGRESIVA",
                        title: "Faltan",
                        visible: true,
                        order: 20,
                        config: {
                            counterX: 50,
                            counterY: 65,
                            counterWidth: 90,
                        },
                    },
                ],
            },
        },
        canvases: [],
    };
}

test("detecta migración pendiente", () => {
    assert.equal(isLegacyMigrationPending(documentWithLegacy()), true);
});

test("convierte sections en canvases ordenados", () => {
    const result = migrateLegacyDocument(documentWithLegacy(), {
        idFactory: (() => {
            let id = 0;
            return (prefix) => `${prefix}-${++id}`;
        })(),
    });

    assert.equal(result.migrated, true);
    assert.equal(result.document.canvases.length, 2);
    assert.equal(result.document.canvases[0].type, "PORTADA");
    assert.equal(result.document.canvases[1].type, "CUENTA_REGRESIVA");
    assert.equal(result.document.globals.legacyMigrationPending, false);
    assert.equal(result.document.globals.legacyEditorConfig, undefined);
});

test("conserva fondo, textos y capas personalizadas", () => {
    const result = migrateLegacyDocument(documentWithLegacy());
    const nodes = result.document.canvases[0].nodes;

    assert.equal(nodes.some((node) => node.type === "IMAGE"), true);
    assert.equal(nodes.filter((node) => node.type === "TEXT").length >= 3, true);
    assert.equal(result.document.assets[0].url, "/media/portada.jpg");
});

test("countdown migra como jerarquía editable", () => {
    const result = migrateLegacyDocument(documentWithLegacy());
    const countdown = result.document.canvases[1].nodes.find(
        (node) => node.type === "COUNTDOWN",
    );

    assert.ok(countdown);
    assert.equal(countdown.children.length, 4);
    assert.equal(countdown.children[0].type, "CARD");
    assert.equal(countdown.children[0].children.length, 2);
});

test("es idempotente después de migrar", () => {
    const first = migrateLegacyDocument(documentWithLegacy());
    const second = migrateLegacyDocument(first.document);

    assert.equal(second.migrated, false);
    assert.equal(second.report.reason, "not-pending");
});
