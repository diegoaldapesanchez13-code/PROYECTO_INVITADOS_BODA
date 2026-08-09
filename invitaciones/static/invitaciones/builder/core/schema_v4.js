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

    const aliases = new Map();

    output.canvases = sections.map((section, index) => {
        const canvas = sectionToCanvas(section, index);
        registerCanvasAliases(aliases, canvas.id, section, canvas);
        return canvas;
    });

    output.nodes = (
        Array.isArray(source.nodes)
            ? source.nodes
            : []
    ).map((rawNode) => {
        const node = clone(rawNode);
        const legacySectionId =
            node.canvasId
            || node.sectionId
            || findCanvasId(node, source, aliases);

        node.canvasId =
            legacySectionId
                ? remapReference(
                    legacySectionId,
                    aliases
                )
                : null;
        node.parentId = remapReference(
            node.parentId,
            aliases
        );
        node.children = remapReferences(
            node.children,
            aliases
        );
        node.interaction = remapInteractionTargets(
            node.interaction,
            aliases
        );

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

    const rawCanvases =
        Array.isArray(source.canvases)
            && source.canvases.length
            ? source.canvases
            : (
                Array.isArray(source.sections)
                    ? source.sections
                    : []
            );

    const aliases = new Map();

    output.canvases = rawCanvases.map((canvas, index) => {
        const normalized = sectionToCanvas(canvas, index);
        registerCanvasAliases(
            aliases,
            normalized.id,
            canvas,
            normalized
        );
        return normalized;
    });

    if (
        Array.isArray(source.sections)
        && Array.isArray(source.canvases)
    ) {
        source.sections.forEach((section, index) => {
            const canvas = output.canvases[index];
            if (canvas) {
                registerCanvasAliases(
                    aliases,
                    canvas.id,
                    section,
                    canvas
                );
            }
        });
    }

    output.nodes = Array.isArray(source.nodes)
        ? source.nodes.map((rawNode) => {
            const node = clone(rawNode);

            node.parentId = remapReference(
                node.parentId,
                aliases
            );
            node.canvasId = remapReference(
                node.canvasId ?? node.sectionId,
                aliases
            );
            node.children = remapReferences(
                node.children,
                aliases
            );
            node.interaction = remapInteractionTargets(
                node.interaction,
                aliases
            );

            delete node.sectionId;

            if (node.coordinateSpace === "SECTION") {
                node.coordinateSpace = "CANVAS";
            }

            return node;
        })
        : [];

    normalizeHierarchy(output);

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
    const allIds = new Set(canvasIds);
    for (const node of document.nodes || []) {
        if (!node?.id) {
            errors.push("Cada nodo requiere id.");
            continue;
        }

        if (nodeIds.has(String(node.id))) {
            errors.push(`Nodo duplicado: ${node.id}`);
        }

        nodeIds.add(String(node.id));
        allIds.add(String(node.id));

        if (
            node.canvasId != null
            && !canvasIds.has(String(node.canvasId))
        ) {
            errors.push(
                `Nodo ${node.id} referencia canvas inexistente ${node.canvasId}.`
            );
        }
    }

    for (const node of [
        ...(document.canvases || []),
        ...(document.nodes || []),
    ]) {
        if (
            node.parentId != null
            && !allIds.has(String(node.parentId))
        ) {
            errors.push(
                `Nodo ${node.id} referencia parent inexistente ${node.parentId}.`
            );
        }

        for (const childId of node.children || []) {
            if (!allIds.has(String(childId))) {
                errors.push(
                    `Nodo ${node.id} referencia hijo inexistente ${childId}.`
                );
            }
        }
    }

    for (const cycle of detectCycles([
        ...(document.canvases || []),
        ...(document.nodes || []),
    ])) {
        errors.push(
            `Ciclo detectado: ${cycle.join(" -> ")}`
        );
    }

    if (document.responsive?.baseDevice !== "mobile") {
        errors.push("V4 debe ser mobile-first.");
    }

    return {
        valid: errors.length === 0,
        errors,
    };
}

function sectionToCanvas(section, index) {
    const canvas = clone(section);
    const id =
        canvas.id
        || canvas.canvasId
        || canvas.sectionId
        || `canvas-${index}`;

    canvas.id = String(id);
    canvas.type = V4_NODE_TYPES.CANVAS;
    canvas.order = finiteInteger(canvas.order, index);
    canvas.parentId = null;
    canvas.canvasId = canvas.id;
    canvas.layoutMode = "FLOW";
    canvas.coordinateSpace = "CANVAS";
    canvas.x = 50;
    canvas.y = 50;
    canvas.width = 100;
    canvas.rotation = 0;
    canvas.scale = 1;
    canvas.children = remapReferences(canvas.children);
    delete canvas.sectionId;

    return canvas;
}

function registerCanvasAliases(aliases, canvasId, ...sources) {
    for (const source of sources) {
        if (!source || typeof source !== "object") {
            continue;
        }

        for (
            const key of [
                "id",
                "canvasId",
                "sectionId",
                "r3Id",
            ]
        ) {
            if (source[key] != null && source[key] !== "") {
                aliases.set(String(source[key]), String(canvasId));
            }
        }

        const legacySectionId =
            source.content?.legacySectionId;

        if (
            legacySectionId != null
            && legacySectionId !== ""
        ) {
            aliases.set(
                String(legacySectionId),
                String(canvasId)
            );
        }
    }

    aliases.set(String(canvasId), String(canvasId));
}

function remapReference(value, aliases = new Map()) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    const key = String(value);
    return aliases.get(key) || key;
}

function remapReferences(values, aliases = new Map()) {
    return Array.isArray(values)
        ? [...new Set(
            values
                .map((value) => remapReference(value, aliases))
                .filter(Boolean)
        )]
        : [];
}

function remapInteractionTargets(interaction, aliases) {
    if (
        !interaction
        || typeof interaction !== "object"
        || Array.isArray(interaction)
    ) {
        return interaction;
    }

    const next = clone(interaction);

    if (
        next.action
        && typeof next.action === "object"
        && !Array.isArray(next.action)
    ) {
        for (const key of ["value", "target", "canvasId"]) {
            if (next.action[key]) {
                next.action[key] = remapReference(
                    next.action[key],
                    aliases
                );
            }
        }

        if (
            next.action.payload
            && typeof next.action.payload === "object"
            && !Array.isArray(next.action.payload)
        ) {
            for (
                const key of [
                    "canvasId",
                    "sectionId",
                    "target",
                ]
            ) {
                if (next.action.payload[key]) {
                    next.action.payload[key] =
                        remapReference(
                            next.action.payload[key],
                            aliases
                        );
                }
            }
        }
    }

    return next;
}

function normalizeHierarchy(document) {
    const allNodes = [
        ...document.canvases,
        ...document.nodes,
    ];
    const byId = new Map(
        allNodes.map((node) => [String(node.id), node])
    );
    const canvasIds = new Set(
        document.canvases.map((canvas) => String(canvas.id))
    );

    for (const node of allNodes) {
        node.children = remapReferences(node.children)
            .filter(
                (childId) =>
                    byId.has(childId)
                    && childId !== String(node.id)
            );
    }

    for (const node of document.nodes) {
        if (!node.canvasId || !canvasIds.has(String(node.canvasId))) {
            node.canvasId = inferCanvasId(node, byId, canvasIds);
        }

        if (!node.parentId || !byId.has(String(node.parentId))) {
            continue;
        }

        const parent = byId.get(String(node.parentId));
        if (!parent.children.includes(String(node.id))) {
            parent.children.push(String(node.id));
        }
    }
}

function inferCanvasId(node, byId, canvasIds) {
    const visited = new Set();
    let current = node;

    while (current?.parentId) {
        const parentId = String(current.parentId);
        if (visited.has(parentId)) break;
        visited.add(parentId);

        if (canvasIds.has(parentId)) {
            return parentId;
        }

        current = byId.get(parentId);
    }

    return node.canvasId == null
        ? null
        : String(node.canvasId);
}

function findCanvasId(node, source, aliases) {
    let current = node;
    const byId = new Map([
        ...(source.sections || []),
        ...(source.nodes || []),
    ].map((item) => [String(item.id), item]));

    while (current?.parentId) {
        const mapped = remapReference(current.parentId, aliases);
        if (mapped && mapped !== String(current.parentId)) {
            return mapped;
        }

        const parent = byId.get(String(current.parentId));
        if (!parent) break;

        if (
            aliases.has(String(parent.id))
            || aliases.has(String(parent.sectionId))
            || parent.type === "SECTION"
        ) {
            return parent.id;
        }

        current = parent;
    }

    return null;
}

function detectCycles(nodes) {
    const byId = new Map(
        nodes.map((node) => [String(node.id), node])
    );
    const cycles = [];
    const visiting = new Set();
    const visited = new Set();

    function visit(id, path) {
        if (visiting.has(id)) {
            const index = path.indexOf(id);
            cycles.push([...path.slice(index), id]);
            return;
        }

        if (visited.has(id)) return;

        visiting.add(id);

        const node = byId.get(id);
        for (const childId of node?.children || []) {
            if (byId.has(String(childId))) {
                visit(String(childId), [...path, id]);
            }
        }

        visiting.delete(id);
        visited.add(id);
    }

    for (const node of nodes) {
        visit(String(node.id), []);
    }

    return cycles;
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
