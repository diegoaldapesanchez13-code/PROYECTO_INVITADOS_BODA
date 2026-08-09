export const SCHEMA_V4_VERSION = 4;

export const V4_NODE_TYPES = Object.freeze({
    CANVAS: "CANVAS",
});

export const V4_DEVICE_KEYS = Object.freeze([
    "mobile",
    "tablet",
    "desktop",
]);

export function createEmptyDocumentV4(overrides = {}) {
    return {
        schemaVersion: SCHEMA_V4_VERSION,
        page: {
            id: "page",
            name: "Invitación",
            type: "PAGE",
            settings: {},
            ...clone(overrides.page || {}),
        },
        canvases: [],
        nodes: [],
        assets: [],
        responsive: {
            baseDevice: "mobile",
            inheritance: {
                tablet: "mobile",
                desktop: "tablet",
            },
            ...clone(overrides.responsive || {}),
        },
        meta: {
            sourceSchemaVersion: null,
            migratedAt: null,
            ...clone(overrides.meta || {}),
        },
    };
}

export function migrateDocumentToV4(input = {}) {
    const source = clone(input || {});

    if (Number(source.schemaVersion) === SCHEMA_V4_VERSION) {
        return normalizeDocumentV4(source);
    }

    if (Number(source.schemaVersion || 3) !== 3) {
        throw new Error(
            `No existe migración a V4 desde schema ${source.schemaVersion}.`
        );
    }

    const output = createEmptyDocumentV4({
        page: source.page || {},
        responsive: {
            baseDevice: "mobile",
            inheritance: {
                tablet: "mobile",
                desktop: "tablet",
            },
        },
        meta: {
            ...(source.meta || {}),
            sourceSchemaVersion: 3,
            migratedAt:
                source.meta?.migratedAt
                || new Date().toISOString(),
        },
    });

    output.assets = Array.isArray(source.assets)
        ? clone(source.assets)
        : [];

    const sections = Array.isArray(source.sections)
        ? source.sections
        : [];

    output.canvases = sections.map((section, index) => {
        const canvas = clone(section);
        canvas.type = V4_NODE_TYPES.CANVAS;
        canvas.order = finiteInteger(canvas.order, index);
        canvas.parentId = null;
        canvas.canvasId = canvas.id;
        delete canvas.sectionId;

        if (canvas.coordinateSpace === "SECTION") {
            canvas.coordinateSpace = "CANVAS";
        }

        return canvas;
    });

    const canvasIds = new Set(
        output.canvases.map((canvas) => String(canvas.id))
    );

    output.nodes = (
        Array.isArray(source.nodes)
            ? source.nodes
            : []
    ).map((rawNode) => {
        const node = clone(rawNode);
        const legacySectionId =
            node.sectionId
            || findCanvasId(node, source, canvasIds);

        node.canvasId =
            legacySectionId
                ? String(legacySectionId)
                : null;

        delete node.sectionId;

        if (node.coordinateSpace === "SECTION") {
            node.coordinateSpace = "CANVAS";
        }

        return node;
    });

    return normalizeDocumentV4(output);
}

export function normalizeDocumentV4(input = {}) {
    const source = clone(input || {});
    const output = createEmptyDocumentV4({
        page: source.page || {},
        responsive: source.responsive || {},
        meta: source.meta || {},
    });

    output.schemaVersion = SCHEMA_V4_VERSION;
    output.assets = Array.isArray(source.assets)
        ? clone(source.assets)
        : [];
    output.canvases = Array.isArray(source.canvases)
        ? source.canvases.map((canvas, index) => ({
            ...clone(canvas),
            type: V4_NODE_TYPES.CANVAS,
            parentId: null,
            canvasId: String(canvas.canvasId || canvas.id),
            order: finiteInteger(canvas.order, index),
        }))
        : [];
    output.nodes = Array.isArray(source.nodes)
        ? source.nodes.map((node) => ({
            ...clone(node),
            canvasId:
                node.canvasId == null
                    ? null
                    : String(node.canvasId),
        }))
        : [];

    output.responsive = {
        baseDevice: "mobile",
        inheritance: {
            tablet: "mobile",
            desktop: "tablet",
        },
        ...clone(source.responsive || {}),
    };

    // V4 is always mobile-first even if a malformed document tries to
    // reintroduce the previous inheritance direction.
    output.responsive.baseDevice = "mobile";
    output.responsive.inheritance = {
        tablet: "mobile",
        desktop: "tablet",
    };

    return output;
}

export function validateDocumentV4(document) {
    const errors = [];

    if (!document || typeof document !== "object") {
        return {
            valid: false,
            errors: ["Documento V4 inválido."],
        };
    }

    if (document.schemaVersion !== SCHEMA_V4_VERSION) {
        errors.push("schemaVersion debe ser 4.");
    }

    if (!Array.isArray(document.canvases)) {
        errors.push("canvases debe ser un arreglo.");
    }

    if (!Array.isArray(document.nodes)) {
        errors.push("nodes debe ser un arreglo.");
    }

    const canvasIds = new Set();
    for (const canvas of document.canvases || []) {
        if (!canvas?.id) {
            errors.push("Cada canvas requiere id.");
            continue;
        }

        if (canvasIds.has(String(canvas.id))) {
            errors.push(`Canvas duplicado: ${canvas.id}`);
        }

        canvasIds.add(String(canvas.id));

        if (canvas.type !== V4_NODE_TYPES.CANVAS) {
            errors.push(`Canvas ${canvas.id} debe tener type CANVAS.`);
        }
    }

    const nodeIds = new Set();
    for (const node of document.nodes || []) {
        if (!node?.id) {
            errors.push("Cada nodo requiere id.");
            continue;
        }

        if (nodeIds.has(String(node.id))) {
            errors.push(`Nodo duplicado: ${node.id}`);
        }

        nodeIds.add(String(node.id));

        if (
            node.canvasId != null
            && !canvasIds.has(String(node.canvasId))
        ) {
            errors.push(
                `Nodo ${node.id} referencia canvas inexistente ${node.canvasId}.`
            );
        }
    }

    if (document.responsive?.baseDevice !== "mobile") {
        errors.push("V4 debe ser mobile-first.");
    }

    return {
        valid: errors.length === 0,
        errors,
    };
}

function findCanvasId(node, source, canvasIds) {
    let current = node;
    const byId = new Map([
        ...(source.sections || []),
        ...(source.nodes || []),
    ].map((item) => [String(item.id), item]));

    while (current?.parentId) {
        const parent = byId.get(String(current.parentId));
        if (!parent) break;

        if (
            canvasIds.has(String(parent.id))
            || parent.type === "SECTION"
        ) {
            return parent.id;
        }

        current = parent;
    }

    return null;
}

function finiteInteger(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number)
        ? Math.trunc(number)
        : fallback;
}

function clone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
