import {
    NODE_TYPES,
} from "./schema.js";

export const COMPONENT_CAPABILITIES = Object.freeze({
    CONTAINER: "CONTAINER",
    AUTO_LAYOUT: "AUTO_LAYOUT",
    CONSTRAINTS: "CONSTRAINTS",
    TRANSFORM: "TRANSFORM",
    MEDIA: "MEDIA",
    ACTIONABLE: "ACTIONABLE",
    DYNAMIC_DATA: "DYNAMIC_DATA",
});

const DEFINITIONS = Object.freeze([
    definition(NODE_TYPES.PAGE, {
        label: "Documento",
        icon: "PG",
        element: "main",
        inspectorPanel: null,
        capabilities: [],
    }),
    definition(NODE_TYPES.SECTION, {
        label: "Lienzo",
        icon: "LZ",
        element: "section",
        inspectorPanel: "section",
        capabilities: [
            COMPONENT_CAPABILITIES.CONTAINER,
            COMPONENT_CAPABILITIES.AUTO_LAYOUT,
        ],
    }),
    definition(NODE_TYPES.BACKGROUND, {
        label: "Fondo heredado",
        icon: "BG",
        element: "div",
        inspectorPanel: "background",
        capabilities: [],
        legacy: true,
    }),
    definition(NODE_TYPES.OVERLAY, {
        label: "Overlay",
        icon: "OV",
        element: "div",
        inspectorPanel: null,
        capabilities: [],
    }),
    definition(NODE_TYPES.CONTAINER, {
        label: "Contenedor",
        icon: "CT",
        element: "div",
        inspectorPanel: "card",
        capabilities: [
            COMPONENT_CAPABILITIES.CONTAINER,
            COMPONENT_CAPABILITIES.AUTO_LAYOUT,
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
        ],
    }),
    definition(NODE_TYPES.CARD, {
        label: "Card",
        icon: "CD",
        element: "div",
        inspectorPanel: "card",
        capabilities: [
            COMPONENT_CAPABILITIES.CONTAINER,
            COMPONENT_CAPABILITIES.AUTO_LAYOUT,
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.TEXT, {
        label: "Texto",
        icon: "T",
        element: "p",
        inspectorPanel: "text",
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.ACTIONABLE,
            COMPONENT_CAPABILITIES.DYNAMIC_DATA,
        ],
    }),
    definition(NODE_TYPES.IMAGE, {
        label: "Imagen",
        icon: "IM",
        element: "img",
        inspectorPanel: "image",
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.MEDIA,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.BUTTON, {
        label: "Botón",
        icon: "BT",
        element: "a",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.MAP, {
        label: "Google Maps",
        icon: "MP",
        element: "div",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.ACTIONABLE,
            COMPONENT_CAPABILITIES.DYNAMIC_DATA,
        ],
    }),
    definition(NODE_TYPES.COUNTDOWN, {
        label: "Cuenta regresiva",
        icon: "CDN",
        element: "div",
        inspectorPanel: "countdown",
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.DYNAMIC_DATA,
        ],
        customRenderer: "countdown",
    }),
    definition(NODE_TYPES.GALLERY, {
        label: "Galería",
        icon: "GL",
        element: "div",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONTAINER,
            COMPONENT_CAPABILITIES.AUTO_LAYOUT,
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.MEDIA,
        ],
    }),
    definition(NODE_TYPES.RSVP, {
        label: "RSVP",
        icon: "RS",
        element: "div",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONTAINER,
            COMPONENT_CAPABILITIES.AUTO_LAYOUT,
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.DYNAMIC_DATA,
        ],
    }),
    definition(NODE_TYPES.DECORATION, {
        label: "Decoración",
        icon: "DC",
        element: "img",
        inspectorPanel: "decoration",
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.MEDIA,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.VIDEO, {
        label: "Video",
        icon: "VD",
        element: "video",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.MEDIA,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.ICON, {
        label: "Icono",
        icon: "IC",
        element: "span",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
            COMPONENT_CAPABILITIES.ACTIONABLE,
        ],
    }),
    definition(NODE_TYPES.SEPARATOR, {
        label: "Separador",
        icon: "—",
        element: "hr",
        inspectorPanel: null,
        capabilities: [
            COMPONENT_CAPABILITIES.CONSTRAINTS,
            COMPONENT_CAPABILITIES.TRANSFORM,
        ],
    }),
]);

const REGISTRY = new Map(
    DEFINITIONS.map((item) => [item.type, item])
);

export function getComponentDefinition(type) {
    const item = REGISTRY.get(String(type || ""));
    return item ? clone(item) : null;
}

export function requireComponentDefinition(type) {
    const item = getComponentDefinition(type);

    if (!item) {
        throw new Error(`Componente no registrado: ${type}`);
    }

    return item;
}

export function listComponentDefinitions(options = {}) {
    const {
        includeLegacy = true,
    } = options;

    return DEFINITIONS
        .filter((item) => includeLegacy || !item.legacy)
        .map(clone);
}

export function componentSupports(type, capability) {
    const item = REGISTRY.get(String(type || ""));

    return Boolean(
        item
        && item.capabilities.includes(capability)
    );
}

export function isContainerComponent(type) {
    return componentSupports(
        type,
        COMPONENT_CAPABILITIES.CONTAINER
    );
}

export function componentElementName(type) {
    return REGISTRY.get(String(type || ""))?.element || "div";
}

export function componentIcon(type) {
    return REGISTRY.get(String(type || ""))?.icon || "?";
}

export function componentLabel(type) {
    return REGISTRY.get(String(type || ""))?.label || String(type || "Componente");
}

function definition(type, options) {
    return Object.freeze({
        type,
        label: String(options.label || type),
        icon: String(options.icon || "?"),
        element: String(options.element || "div"),
        inspectorPanel:
            options.inspectorPanel === null
                ? null
                : String(options.inspectorPanel || ""),
        customRenderer:
            options.customRenderer
                ? String(options.customRenderer)
                : null,
        legacy: Boolean(options.legacy),
        capabilities: Object.freeze([
            ...new Set(options.capabilities || []),
        ]),
    });
}

function clone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
