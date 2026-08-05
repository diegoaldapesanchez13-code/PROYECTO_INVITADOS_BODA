import {
    INTERACTION_TYPES,
} from "./defaults.js";

const DEFINITIONS = Object.freeze([
    definition(INTERACTION_TYPES.NONE, {
        label: "Ninguna",
        valueControl: "hidden",
        placeholder: "",
        supportsNewTab: false,
        executor: INTERACTION_TYPES.NONE,
    }),
    definition(INTERACTION_TYPES.URL, {
        label: "Abrir URL",
        valueControl: "text",
        placeholder: "https://...",
        supportsNewTab: true,
        executor: INTERACTION_TYPES.URL,
    }),
    definition(INTERACTION_TYPES.GOOGLE_MAPS, {
        label: "Google Maps",
        valueControl: "text",
        placeholder: "https://maps.app.goo.gl/...",
        supportsNewTab: true,
        executor: INTERACTION_TYPES.GOOGLE_MAPS,
    }),
    definition(INTERACTION_TYPES.WHATSAPP, {
        label: "WhatsApp",
        valueControl: "text",
        valueLabel: "Número",
        placeholder: "5214771234567",
        targetControl: "textarea",
        targetLabel: "Mensaje opcional",
        targetPlaceholder: "Hola, confirmo mi asistencia.",
        supportsNewTab: true,
        executor: INTERACTION_TYPES.WHATSAPP,
    }),
    definition(INTERACTION_TYPES.SECTION, {
        label: "Ir a lienzo",
        valueControl: "section",
        placeholder: "ID del lienzo",
        supportsNewTab: false,
        executor: INTERACTION_TYPES.SECTION,
    }),
]);

const REGISTRY = new Map(
    DEFINITIONS.map((item) => [item.type, item])
);

export function listInteractionDefinitions() {
    return DEFINITIONS.map(clone);
}

export function getInteractionDefinition(type) {
    const item = REGISTRY.get(String(type || ""));
    return item ? clone(item) : null;
}

export function requireInteractionDefinition(type) {
    const item = getInteractionDefinition(type);

    if (!item) {
        throw new Error(
            `Interacción no registrada: ${type}`
        );
    }

    return item;
}

export function interactionTypeOptions() {
    return DEFINITIONS.map((item) => [
        item.type,
        item.label,
    ]);
}

function definition(type, values) {
    return Object.freeze({
        type,
        label: String(values.label || type),
        valueControl:
            values.valueControl || "text",
        valueLabel:
            String(values.valueLabel || "Valor"),
        placeholder:
            String(values.placeholder || ""),
        targetControl:
            values.targetControl || "hidden",
        targetLabel:
            String(values.targetLabel || "Destino"),
        targetPlaceholder:
            String(values.targetPlaceholder || ""),
        supportsNewTab:
            Boolean(values.supportsNewTab),
        executor:
            String(values.executor || type),
    });
}

function clone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
