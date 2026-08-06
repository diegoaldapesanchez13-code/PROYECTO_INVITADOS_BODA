import { COMPONENT_CONTRACT_VERSION } from "./constants.js";

export function normalizeComponentDefinition(raw = {}) {
    const type = normalizeType(raw.type);
    const definition = {
        contractVersion: COMPONENT_CONTRACT_VERSION,
        version: String(raw.version || "1.0.0"),
        type,
        label: String(raw.label || type),
        icon: String(raw.icon || "?"),
        element: String(raw.element || "div"),
        category: String(raw.category || "general"),
        inspector: raw.inspector == null ? null : String(raw.inspector),
        renderer: raw.renderer == null ? type : String(raw.renderer),
        legacy: Boolean(raw.legacy),
        capabilities: Object.freeze(uniqueStrings(raw.capabilities)),
        defaults: cloneObject(raw.defaults),
        migrations: Object.freeze(Array.isArray(raw.migrations) ? [...raw.migrations] : []),
        factory: typeof raw.factory === "function" ? raw.factory : null,
        validate: typeof raw.validate === "function" ? raw.validate : null,
    };
    return Object.freeze(definition);
}

export function validateComponentDefinition(raw) {
    const errors = [];
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
        return { valid: false, errors: ["La definición debe ser un objeto."] };
    }
    if (!String(raw.type || "").trim()) errors.push("type es obligatorio.");
    if (raw.factory != null && typeof raw.factory !== "function") {
        errors.push("factory debe ser una función.");
    }
    if (raw.validate != null && typeof raw.validate !== "function") {
        errors.push("validate debe ser una función.");
    }
    if (raw.capabilities != null && !Array.isArray(raw.capabilities)) {
        errors.push("capabilities debe ser un arreglo.");
    }
    return { valid: errors.length === 0, errors };
}

function normalizeType(value) {
    const type = String(value || "").trim().toUpperCase();
    if (!type) throw new TypeError("El tipo del componente es obligatorio.");
    return type;
}
function uniqueStrings(values = []) {
    return [...new Set(values.map((value) => String(value || "").trim()).filter(Boolean))];
}
function cloneObject(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
