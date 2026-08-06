import {
    INTERACTION_CONTRACT_VERSION,
    INTERACTION_TRIGGERS,
    INTERACTION_TYPES,
} from "./constants.js";

export function createInteraction(overrides = {}) {
    const action = plainObject(overrides.action);
    return Object.freeze({
        contractVersion: INTERACTION_CONTRACT_VERSION,
        enabled: Boolean(overrides.enabled ?? false),
        trigger: enumValue(
            overrides.trigger,
            Object.values(INTERACTION_TRIGGERS),
            INTERACTION_TRIGGERS.CLICK,
        ),
        action: Object.freeze({
            type: enumValue(
                action.type,
                Object.values(INTERACTION_TYPES),
                INTERACTION_TYPES.NONE,
            ),
            value: stringValue(action.value),
            target: stringValue(action.target),
            openInNewTab: Boolean(action.openInNewTab ?? false),
            payload: cloneObject(action.payload),
        }),
    });
}

export function validateInteraction(value) {
    const errors = [];
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return { valid: false, errors: ["La interacción debe ser un objeto."] };
    }
    const normalized = createInteraction(value);
    if (!Object.values(INTERACTION_TRIGGERS).includes(normalized.trigger)) {
        errors.push("trigger no es válido.");
    }
    if (!Object.values(INTERACTION_TYPES).includes(normalized.action.type)) {
        errors.push("action.type no es válido.");
    }
    return { valid: errors.length === 0, errors, value: normalized };
}

function enumValue(value, allowed, fallback) {
    const normalized = String(value || "").toUpperCase();
    return allowed.includes(normalized) ? normalized : fallback;
}
function stringValue(value) {
    return value == null ? "" : String(value);
}
function plainObject(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}
function cloneObject(value) {
    const source = plainObject(value);
    if (typeof structuredClone === "function") return structuredClone(source);
    return JSON.parse(JSON.stringify(source));
}
