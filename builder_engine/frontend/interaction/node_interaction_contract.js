import {
    INTERACTION_TRIGGERS,
    INTERACTION_TYPES,
} from "./constants.js";

export const NODE_INTERACTION_CONTRACT_VERSION = 2;

export const INTERACTION_STATES = Object.freeze({
    DEFAULT: "default",
    HOVER: "hover",
    PRESSED: "pressed",
    DISABLED: "disabled",
});

export function createNodeInteractionContract(raw = {}) {
    const interactions = Array.isArray(raw.interactions)
        ? raw.interactions.map(normalizeInteraction)
        : [];

    return {
        contractVersion: NODE_INTERACTION_CONTRACT_VERSION,
        focusable: raw.focusable !== false && interactions.length > 0,
        ariaLabel: String(raw.ariaLabel || ""),
        interactions,
        states: normalizeStates(raw.states),
    };
}

export function normalizeInteraction(raw = {}) {
    const action = object(raw.action);
    return {
        id: String(raw.id || createId()),
        enabled: raw.enabled !== false,
        trigger: enumValue(
            raw.trigger,
            Object.values(INTERACTION_TRIGGERS),
            INTERACTION_TRIGGERS.CLICK,
        ),
        action: {
            type: enumValue(
                action.type,
                Object.values(INTERACTION_TYPES),
                INTERACTION_TYPES.NONE,
            ),
            value: String(action.value || ""),
            target: String(action.target || ""),
            openInNewTab: Boolean(action.openInNewTab),
            payload: cloneObject(action.payload),
        },
    };
}

export function nodeIsActionable(node = {}) {
    const contract = createNodeInteractionContract(
        node.interaction || {
            interactions: node.interactions,
            states: node.states,
            ariaLabel: node.ariaLabel,
        },
    );

    return contract.interactions.some(
        (interaction) => interaction.enabled
            && interaction.action.type !== INTERACTION_TYPES.NONE,
    );
}

export function validateNodeInteractionContract(value) {
    const errors = [];
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return { valid: false, errors: ["NodeInteraction debe ser un objeto."] };
    }

    const normalized = createNodeInteractionContract(value);
    normalized.interactions.forEach((interaction, index) => {
        if (
            interaction.enabled
            && interaction.action.type === INTERACTION_TYPES.NONE
        ) {
            errors.push(`interactions[${index}] está habilitada pero no tiene acción.`);
        }
    });

    return { valid: errors.length === 0, errors, value: normalized };
}

function normalizeStates(raw = {}) {
    const source = object(raw);
    return {
        default: cloneObject(source.default),
        hover: cloneObject(source.hover),
        pressed: cloneObject(source.pressed),
        disabled: cloneObject(source.disabled),
    };
}

function enumValue(value, allowed, fallback) {
    const normalized = String(value || "").toUpperCase();
    return allowed.includes(normalized) ? normalized : fallback;
}

function object(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function cloneObject(value) {
    const source = object(value);
    if (typeof structuredClone === "function") return structuredClone(source);
    return JSON.parse(JSON.stringify(source));
}

function createId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `interaction-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}
