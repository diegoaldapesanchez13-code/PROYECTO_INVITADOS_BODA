import assert from "node:assert/strict";
import test from "node:test";

import {
    migrateDocumentToV4,
    normalizeDocumentV4,
    validateDocumentV4,
} from "../core/schema_v4.js";

function v3Fixture() {
    return {
        schemaVersion: 3,
        page: {
            id: "page-1",
            name: "Boda",
            type: "PAGE",
            settings: {},
        },
        sections: [
            {
                id: "section-1",
                type: "SECTION",
                name: "Portada",
                sectionId: "section-1",
                parentId: null,
                order: 0,
                coordinateSpace: "SECTION",
                children: ["image-1"],
            },
        ],
        nodes: [
            {
                id: "image-1",
                type: "IMAGE",
                parentId: "section-1",
                sectionId: "section-1",
                order: 0,
                coordinateSpace: "SECTION",
                x: 50,
                y: 50,
                width: 80,
                height: 50,
                interaction: {
                    enabled: true,
                    action: {
                        type: "URL",
                        payload: {
                            url: "https://example.com",
                        },
                    },
                },
                responsive: {
                    mobile: {
                        style: {
                            opacity: 0.9,
                        },
                    },
                },
                children: [],
            },
        ],
        assets: [
            {
                id: "db-1",
                url: "/media/foto.jpg",
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
            source: "R3",
        },
    };
}

test("V3 migra a V4 sin perder ids, assets ni interacción", () => {
    const source = v3Fixture();
    const migrated = migrateDocumentToV4(source);

    assert.equal(migrated.schemaVersion, 4);
    assert.equal(migrated.canvases[0].id, "section-1");
    assert.equal(migrated.canvases[0].type, "CANVAS");
    assert.equal(migrated.nodes[0].id, "image-1");
    assert.equal(migrated.nodes[0].canvasId, "section-1");
    assert.equal(migrated.assets[0].id, "db-1");
    assert.deepEqual(
        migrated.nodes[0].interaction,
        source.nodes[0].interaction,
    );
});

test("V4 es mobile-first", () => {
    const migrated = migrateDocumentToV4(v3Fixture());

    assert.equal(
        migrated.responsive.baseDevice,
        "mobile",
    );
    assert.deepEqual(
        migrated.responsive.inheritance,
        {
            tablet: "mobile",
            desktop: "tablet",
        },
    );
});

test("migración no muta el Documento V3", () => {
    const source = v3Fixture();
    const before = JSON.stringify(source);

    migrateDocumentToV4(source);

    assert.equal(JSON.stringify(source), before);
});

test("migración V4 es idempotente", () => {
    const first = migrateDocumentToV4(v3Fixture());
    const second = migrateDocumentToV4(first);

    const firstComparable = structuredClone(first);
    const secondComparable = structuredClone(second);

    assert.deepEqual(secondComparable, firstComparable);
});

test("validator V4 detecta canvas inexistente", () => {
    const document = normalizeDocumentV4({
        schemaVersion: 4,
        canvases: [],
        nodes: [
            {
                id: "text-1",
                type: "TEXT",
                canvasId: "missing",
            },
        ],
    });

    const result = validateDocumentV4(document);

    assert.equal(result.valid, false);
    assert.match(
        result.errors.join("\n"),
        /canvas inexistente/,
    );
});

test("Documento V4 válido pasa validación", () => {
    const document = migrateDocumentToV4(v3Fixture());
    const result = validateDocumentV4(document);

    assert.equal(result.valid, true);
    assert.deepEqual(result.errors, []);
});
