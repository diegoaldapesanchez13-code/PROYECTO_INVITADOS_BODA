import {
    normalizeInteraction,
} from "../interaction/index.js";
import {
    normalizeExperience,
    validateExperience,
} from "../experience/contract.js?v=f4-native-v4-freeze";

export const SCHEMA_VERSION = 4;

export const NODE_TYPES = Object.freeze({
    PAGE: "PAGE",
    CANVAS: "CANVAS",
    BACKGROUND: "BACKGROUND",
    OVERLAY: "OVERLAY",
    CONTAINER: "CONTAINER",
    CARD: "CARD",
    TEXT: "TEXT",
    IMAGE: "IMAGE",
    BUTTON: "BUTTON",
    MAP: "MAP",
    COUNTDOWN: "COUNTDOWN",
    GALLERY: "GALLERY",
    RSVP: "RSVP",
    DECORATION: "DECORATION",
    VIDEO: "VIDEO",
    ICON: "ICON",
    SEPARATOR: "SEPARATOR",
});

export const LAYOUT_MODES = Object.freeze({
    FLOW: "FLOW",
    ABSOLUTE: "ABSOLUTE",
    LAYER: "LAYER",
});

export const COORDINATE_SPACES = Object.freeze({
    CANVAS: "CANVAS",
    PARENT: "PARENT",
});

export const DEVICE_KEYS = Object.freeze([
    "mobile",
    "tablet",
    "desktop",
]);

export function createId(prefix = "node") {
    if (
        typeof globalThis.crypto !== "undefined"
        && typeof globalThis.crypto.randomUUID === "function"
    ) {
        return `${prefix}-${globalThis.crypto.randomUUID()}`;
    }

    const random = Math.random().toString(36).slice(2, 10);
    const time = Date.now().toString(36);
    return `${prefix}-${time}-${random}`;
}

export function createEmptyDocument(overrides = {}) {
    return {
        schemaVersion: SCHEMA_VERSION,
        page: {
            id: createId("page"),
            name: "Invitación",
            type: NODE_TYPES.PAGE,
            settings: {},
            ...structuredCloneSafe(overrides.page || {}),
        },
        experience: normalizeExperience(overrides.experience),
        canvases: [],
        nodes: [],
        assets: [],
        responsive: {
            baseDevice: "mobile",
            inheritance: {
                tablet: "mobile",
                desktop: "tablet",
            },
            ...structuredCloneSafe(overrides.responsive || {}),
        },
        meta: {
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            source: "V4",
            ...structuredCloneSafe(overrides.meta || {}),
        },
    };
}

export function createNode(type, overrides = {}) {
    assertNodeType(type);

    const defaults = {
        id: createId(type.toLowerCase()),
        type,
        name: defaultNodeName(type),
        parentId: null,
        canvasId: null,
        order: 0,
        visible: true,
        locked: false,
        layoutMode: defaultLayoutMode(type),
        coordinateSpace: defaultCoordinateSpace(type),
        x: 50,
        y: 50,
        width: defaultWidth(type),
        height: defaultHeight(type),
        minHeight: 0,
        maxHeight: 0,
        rotation: 0,
        scale: 1,
        opacity: 1,
        zIndex: defaultZIndex(type),
        style: {},
        content: {},
        interaction: normalizeInteraction(),
        responsive: {},
        children: [],
    };

    return normalizeNode({
        ...defaults,
        ...structuredCloneSafe(overrides),
        type,
    });
}

export function normalizeNode(rawNode) {
    const node = {
        ...createNodeDefaults(rawNode?.type),
        ...structuredCloneSafe(rawNode || {}),
    };

    assertNodeType(node.type);

    node.id = String(node.id || createId(node.type.toLowerCase()));
    node.name = String(node.name || defaultNodeName(node.type));
    node.parentId = nullableString(node.parentId);
    node.canvasId = nullableString(node.canvasId);
    node.order = integer(node.order, 0);
    node.visible = Boolean(node.visible ?? true);
    node.locked = Boolean(node.locked ?? false);
    node.layoutMode = enumValue(
        node.layoutMode,
        Object.values(LAYOUT_MODES),
        defaultLayoutMode(node.type),
    );
    node.coordinateSpace = enumValue(
        node.coordinateSpace,
        Object.values(COORDINATE_SPACES),
        defaultCoordinateSpace(node.type),
    );
    node.x = number(node.x, 50);
    node.y = number(node.y, 50);
    node.width = dimension(node.width, defaultWidth(node.type));
    node.height = dimension(node.height, defaultHeight(node.type));
    node.minHeight = number(node.minHeight, 0);
    node.maxHeight = number(node.maxHeight, 0);
    node.rotation = number(node.rotation, 0);
    node.scale = number(node.scale, 1);
    node.opacity = clamp(number(node.opacity, 1), 0, 1);
    node.zIndex = integer(node.zIndex, defaultZIndex(node.type));
    node.style = plainObject(node.style);
    node.content = plainObject(node.content);
    node.interaction = normalizeInteraction(
        node.interaction
    );
    node.responsive = plainObject(node.responsive);
    node.children = Array.isArray(node.children)
        ? [...new Set(node.children.map(String))]
        : [];

    if (node.type === NODE_TYPES.CANVAS) {
        node.parentId = null;
        node.canvasId = node.id;
        node.layoutMode = LAYOUT_MODES.FLOW;
        node.coordinateSpace = COORDINATE_SPACES.CANVAS;
        node.x = 50;
        node.y = 50;
        node.width = 100;
        node.rotation = 0;
        node.scale = 1;
    }

    return node;
}

export function normalizeDocument(rawDocument = {}) {
    const document = createEmptyDocument(rawDocument);

    document.schemaVersion = SCHEMA_VERSION;
    document.canvases = Array.isArray(rawDocument.canvases)
        ? rawDocument.canvases.map((canvas) =>
            normalizeNode({
                ...canvas,
                type: NODE_TYPES.CANVAS,
            })
        )
        : [];

    document.nodes = Array.isArray(rawDocument.nodes)
        ? rawDocument.nodes.map(normalizeNode)
        : [];

    document.experience = normalizeExperience(rawDocument.experience);

    expandCompositeCountdowns(document);

    document.assets = Array.isArray(rawDocument.assets)
        ? structuredCloneSafe(rawDocument.assets)
        : [];

    document.meta.updatedAt = new Date().toISOString();

    return document;
}

function expandCompositeCountdowns(document) {
    const existingIds = new Set([
        ...document.canvases.map((node) => node.id),
        ...document.nodes.map((node) => node.id),
    ]);

    for (const countdown of document.nodes.filter(
        (node) => node.type === NODE_TYPES.COUNTDOWN
    )) {
        const actualChildren = (countdown.children || [])
            .filter((id) => existingIds.has(id));

        if (actualChildren.length > 0) {
            countdown.children = actualChildren;
            countdown.content = {
                values: [120, 12, 34, 56],
                labels: ["Días", "Horas", "Minutos", "Segundos"],
                ...countdown.content,
                compositeVersion: 1,
            };
            continue;
        }

        const units = [
            ["days", "Días", 0, 12.5],
            ["hours", "Horas", 1, 37.5],
            ["minutes", "Minutos", 2, 62.5],
            ["seconds", "Segundos", 3, 87.5],
        ];

        countdown.children = [];
        countdown.content = {
            values: [120, 12, 34, 56],
            labels: ["Días", "Horas", "Minutos", "Segundos"],
            ...countdown.content,
            compositeVersion: 1,
        };
        countdown.style = {
            ...countdown.style,
            overflow: "visible",
        };

        for (const [unit, fallbackLabel, index, x] of units) {
            const label = String(
                countdown.content.labels?.[index] ?? fallbackLabel
            );
            const item = createNode(NODE_TYPES.CARD, {
                name: label,
                parentId: countdown.id,
                canvasId: countdown.canvasId,
                order: countdown.children.length,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x, y: 50, width: 23, height: 88, zIndex: 1,
                style: {
                    paddingX: 4, paddingY: 4,
                    backgroundColor: countdown.style?.itemBackgroundColor || "#ffffff",
                    borderColor: countdown.style?.itemBorderColor || "#dfe5db",
                    borderWidth: Number(countdown.style?.itemBorderWidth ?? 1),
                    borderRadius: Number(countdown.style?.itemBorderRadius ?? 16),
                    boxShadow: "none", overflow: "visible",
                },
                content: { countdownUnit: unit },
            });
            const value = createNode(NODE_TYPES.TEXT, {
                name: `${label} · Número`, parentId: item.id,
                canvasId: countdown.canvasId, order: 0,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x: 50, y: 38, width: 92, height: 34, zIndex: 2,
                content: { text: String(countdown.content.values?.[index] ?? 0), tag: "span", binding: { source: "COUNTDOWN", unit, role: "value" } },
                style: { color: countdown.style?.valueColor || "#2f342d", fontFamily: countdown.style?.valueFontFamily || "'Playfair Display', serif", fontSize: Number(countdown.style?.valueSize ?? 30), fontWeight: Number(countdown.style?.valueWeight ?? 700), textAlign: "center", lineHeight: 1, letterSpacing: Number(countdown.style?.valueLetterSpacing ?? 0) },
            });
            const caption = createNode(NODE_TYPES.TEXT, {
                name: `${label} · Etiqueta`, parentId: item.id,
                canvasId: countdown.canvasId, order: 1,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x: 50, y: 72, width: 94, height: 22, zIndex: 3,
                content: { text: label, tag: "span", binding: { source: "COUNTDOWN", unit, role: "label" } },
                style: { color: countdown.style?.labelColor || "#777971", fontFamily: countdown.style?.labelFontFamily || "Montserrat, sans-serif", fontSize: Number(countdown.style?.labelSize ?? 10), fontWeight: Number(countdown.style?.labelWeight ?? 600), textAlign: "center", lineHeight: 1.15, letterSpacing: Number(countdown.style?.labelLetterSpacing ?? 1), textTransform: countdown.style?.labelTransform || "uppercase" },
            });
            item.children = [value.id, caption.id];
            countdown.children.push(item.id);
            document.nodes.push(item, value, caption);
            existingIds.update?.([item.id, value.id, caption.id]);
            existingIds.add(item.id); existingIds.add(value.id); existingIds.add(caption.id);
        }
    }
}

export function validateDocument(document) {
    const errors = [];
    const warnings = [];

    if (!document || typeof document !== "object") {
        return {
            valid: false,
            errors: ["El documento no es un objeto."],
            warnings,
        };
    }

    if (document.schemaVersion !== SCHEMA_VERSION) {
        errors.push(
            `schemaVersion debe ser ${SCHEMA_VERSION}.`
        );
    }

    const allNodes = [
        ...(document.canvases || []),
        ...(document.nodes || []),
    ];

    const ids = new Set();

    for (const node of allNodes) {
        if (!node.id) {
            errors.push("Existe un nodo sin id.");
            continue;
        }

        if (ids.has(node.id)) {
            errors.push(`ID duplicado: ${node.id}`);
        }

        ids.add(node.id);

        if (!Object.values(NODE_TYPES).includes(node.type)) {
            errors.push(
                `Tipo inválido en ${node.id}: ${node.type}`
            );
        }

        if (
            !Object.values(LAYOUT_MODES)
                .includes(node.layoutMode)
        ) {
            errors.push(
                `layoutMode inválido en ${node.id}`
            );
        }

        if (
            !Object.values(COORDINATE_SPACES)
                .includes(node.coordinateSpace)
        ) {
            errors.push(
                `coordinateSpace inválido en ${node.id}`
            );
        }
    }

    for (const node of allNodes) {
        if (node.parentId && !ids.has(node.parentId)) {
            errors.push(
                `Parent inexistente en ${node.id}: ${node.parentId}`
            );
        }

        if (node.canvasId && !ids.has(node.canvasId)) {
            errors.push(
                `Canvas inexistente en ${node.id}: ${node.canvasId}`
            );
        }

        for (const childId of node.children || []) {
            if (!ids.has(childId)) {
                errors.push(
                    `Hijo inexistente en ${node.id}: ${childId}`
                );
            }
        }
    }

    const cycles = detectCycles(allNodes);
    for (const cycle of cycles) {
        errors.push(
            `Ciclo detectado: ${cycle.join(" -> ")}`
        );
    }

    if (!(document.canvases || []).length) {
        warnings.push("El documento no contiene lienzos.");
    }

    const experienceValidation = validateExperience(document.experience);
    if (!experienceValidation.valid) {
        errors.push(...experienceValidation.errors);
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings,
    };
}

export function serializeDocument(document, spacing = 2) {
    const normalized = normalizeDocument(document);
    const validation = validateDocument(normalized);

    if (!validation.valid) {
        throw new Error(
            `Documento inválido:\n${validation.errors.join("\n")}`
        );
    }

    return JSON.stringify(normalized, null, spacing);
}

function createNodeDefaults(type) {
    if (!Object.values(NODE_TYPES).includes(type)) {
        throw new Error(`Tipo de nodo inválido: ${type}`);
    }

    return {
        id: createId(type.toLowerCase()),
        type,
        name: defaultNodeName(type),
        parentId: null,
        canvasId: null,
        order: 0,
        visible: true,
        locked: false,
        layoutMode: defaultLayoutMode(type),
        coordinateSpace: defaultCoordinateSpace(type),
        x: 50,
        y: 50,
        width: defaultWidth(type),
        height: defaultHeight(type),
        minHeight: 0,
        maxHeight: 0,
        rotation: 0,
        scale: 1,
        opacity: 1,
        zIndex: defaultZIndex(type),
        style: {},
        content: {},
        interaction: normalizeInteraction(),
        responsive: {},
        children: [],
    };
}

function defaultNodeName(type) {
    const names = {
        PAGE: "Página",
        CANVAS: "Lienzo",
        BACKGROUND: "Fondo",
        OVERLAY: "Overlay",
        CONTAINER: "Contenedor",
        CARD: "Tarjeta",
        TEXT: "Texto",
        IMAGE: "Imagen",
        BUTTON: "Botón",
        MAP: "Mapa",
        COUNTDOWN: "Cuenta regresiva",
        GALLERY: "Galería",
        RSVP: "RSVP",
        DECORATION: "Decoración",
        VIDEO: "Video",
        ICON: "Icono",
        SEPARATOR: "Separador",
    };

    return names[type] || type;
}

function defaultLayoutMode(type) {
    if (
        [
            NODE_TYPES.BACKGROUND,
            NODE_TYPES.OVERLAY,
            NODE_TYPES.DECORATION,
        ].includes(type)
    ) {
        return LAYOUT_MODES.LAYER;
    }

    if (
        [
            NODE_TYPES.TEXT,
            NODE_TYPES.IMAGE,
            NODE_TYPES.BUTTON,
            NODE_TYPES.ICON,
            NODE_TYPES.SEPARATOR,
        ].includes(type)
    ) {
        return LAYOUT_MODES.ABSOLUTE;
    }

    return LAYOUT_MODES.FLOW;
}

function defaultCoordinateSpace(type) {
    return type === NODE_TYPES.CANVAS
        ? COORDINATE_SPACES.CANVAS
        : COORDINATE_SPACES.PARENT;
}

function defaultWidth(type) {
    if (type === NODE_TYPES.CANVAS) return 100;
    if (type === NODE_TYPES.BACKGROUND) return 100;
    if (type === NODE_TYPES.CONTAINER) return 100;
    if (type === NODE_TYPES.CARD) return 92;
    if (type === NODE_TYPES.TEXT) return 60;
    if (type === NODE_TYPES.IMAGE) return 40;
    if (type === NODE_TYPES.BUTTON) return 30;
    if (type === NODE_TYPES.COUNTDOWN) return 92;
    return 50;
}

function defaultHeight(type) {
    if (
        [
            NODE_TYPES.CANVAS,
            NODE_TYPES.CONTAINER,
            NODE_TYPES.CARD,
            NODE_TYPES.COUNTDOWN,
            NODE_TYPES.GALLERY,
            NODE_TYPES.RSVP,
        ].includes(type)
    ) {
        return "auto";
    }

    return 10;
}

function defaultZIndex(type) {
    if (type === NODE_TYPES.BACKGROUND) return 0;
    if (type === NODE_TYPES.OVERLAY) return 10;
    if (type === NODE_TYPES.DECORATION) return 40;
    return 20;
}

function detectCycles(nodes) {
    const byId = new Map(
        nodes.map((node) => [node.id, node])
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
            visit(childId, [...path, id]);
        }

        visiting.delete(id);
        visited.add(id);
    }

    for (const node of nodes) {
        visit(node.id, []);
    }

    return cycles;
}

function assertNodeType(type) {
    if (!Object.values(NODE_TYPES).includes(type)) {
        throw new Error(`Tipo de nodo inválido: ${type}`);
    }
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}

function nullableString(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }
    return String(value);
}

function enumValue(value, values, fallback) {
    return values.includes(value) ? value : fallback;
}

function plainObject(value) {
    return (
        value
        && typeof value === "object"
        && !Array.isArray(value)
    )
        ? structuredCloneSafe(value)
        : {};
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function integer(value, fallback) {
    return Math.round(number(value, fallback));
}

function dimension(value, fallback) {
    if (value === "auto") return "auto";
    return number(value, fallback);
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
