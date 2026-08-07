export const COMPONENT_LIBRARY_VERSION = 2;

export const COMPONENT_LIBRARY_ITEMS = Object.freeze([
    item("heading", "Título", "Texto", "T", "TEXT", {
        content: { text: "Título principal", tag: "h2" },
        style: { width: 78, height: 12, fontSize: 42, fontWeight: 700, textAlign: "center" },
    }),
    item("subtitle", "Subtítulo", "Texto", "S", "TEXT", {
        content: { text: "Escribe un subtítulo", tag: "h3" },
        style: { width: 74, height: 10, fontSize: 28, fontWeight: 500, textAlign: "center" },
    }),
    item("paragraph", "Párrafo", "Texto", "¶", "TEXT", {
        content: { text: "Agrega aquí la información de tu evento.", tag: "p" },
        style: { width: 82, height: 14, fontSize: 18, lineHeight: 1.5, textAlign: "center" },
    }),
    item("button", "Botón", "Básicos", "B", "BUTTON", {
        content: { label: "Ver más", href: "#" },
        style: { width: 48, height: 8, backgroundColor: "#2f7a4d", color: "#ffffff", borderRadius: 999 },
    }),
    item("image", "Imagen", "Media", "▧", "IMAGE", {
        content: { assetId: null, url: "", alt: "Selecciona una imagen", placeholder: true },
        style: { width: 72, height: 53.33, aspectRatio: 1.35, fit: "cover", borderRadius: 18 },
    }),
    item("video", "Video", "Media", "▶", "VIDEO", {
        content: { assetId: null, sourceType: "upload", source: "", url: "", controls: true, muted: true, placeholder: true },
        style: { width: 78, height: 43.88, aspectRatio: 1.7778, borderRadius: 18 },
    }),
    item("card", "Card", "Estructura", "C", "CARD", {
        style: { width: 82, height: 28, minHeight: 180, backgroundColor: "#ffffff", borderRadius: 24, padding: 22, gap: 12 },
    }),
    item("container", "Contenedor", "Estructura", "□", "CONTAINER", {
        style: { width: 90, height: 34, minHeight: 220, direction: "column", gap: 12 },
    }),
    item("countdown", "Countdown", "Dinámicos", "◷", "countdown", { blueprint: true }),
    item("separator", "Separador", "Básicos", "—", "SEPARATOR", {
        style: { width: 72, height: 2, borderWidth: 1, color: "#8c8c8c" },
    }),
]);

export function groupLibraryItems(items = COMPONENT_LIBRARY_ITEMS) {
    const groups = new Map();
    for (const entry of items) {
        if (!groups.has(entry.category)) groups.set(entry.category, []);
        groups.get(entry.category).push(entry);
    }
    return [...groups.entries()].map(([category, entries]) => ({ category, items: entries }));
}

export function insertionPosition(existingNodes = [], options = {}) {
    options = options || {};
    existingNodes = Array.isArray(existingNodes) ? existingNodes.filter(Boolean) : [];

    const count = countNodes(existingNodes);
    const column = count % 3;
    const row = Math.floor(count / 3) % 5;

    return {
        x: finite(options.x, 50 + ((column - 1) * 5)),
        y: finite(options.y, Math.min(24 + (row * 11), 78)),
        zIndex: finite(options.zIndex, highestZ(existingNodes) + 1),
    };
}

export function componentInsertOptions(itemDefinition, canvas, options = {}) {
    options = options || {};
    if (!itemDefinition) throw new TypeError("El componente es obligatorio.");
    if (!canvas?.id) throw new TypeError("El lienzo activo es obligatorio.");

    const position = insertionPosition(canvas.nodes || [], options.position || {});
    const definition = clone(itemDefinition);

    if (definition.blueprint) {
        return {
            typeOrBlueprint: definition.type,
            options: {
                blueprint: true,
                context: { canvasId: canvas.id, position, device: options.device || "mobile" },
                label: `Agregar ${definition.label}`,
            },
        };
    }

    return {
        typeOrBlueprint: definition.type,
        options: {
            overrides: {
                ...(definition.overrides || {}),
                name: definition.label,
                style: { ...(definition.overrides?.style || {}), ...position },
            },
            context: { canvasId: canvas.id, position, device: options.device || "mobile" },
            label: `Agregar ${definition.label}`,
        },
    };
}

function item(id, label, category, icon, type, config = {}) {
    return Object.freeze({
        id, label, category, icon, type,
        blueprint: Boolean(config.blueprint),
        overrides: config.blueprint ? {} : clone(config),
    });
}

function countNodes(nodes = []) {
    return nodes.filter(Boolean).reduce(
        (total, node) => total + 1 + countNodes(Array.isArray(node.children) ? node.children : []), 0
    );
}

function highestZ(nodes = []) {
    return nodes.filter(Boolean).reduce((highest, node) => {
        const current = Number(node?.style?.zIndex || 0);
        return Math.max(highest, current, highestZ(Array.isArray(node?.children) ? node.children : []));
    }, 0);
}

function finite(value, fallback) {
    const parsed = Number(value);
    return value !== null && value !== "" && Number.isFinite(parsed) ? parsed : fallback;
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
