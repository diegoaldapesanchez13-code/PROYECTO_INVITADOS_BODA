export const DOCUMENT_SCHEMA_VERSION = 1;
export const BUILDER_ENGINE_VERSION = "0.9.0";

export function createDocument(overrides = {}) {
    const now = new Date().toISOString();
    return normalizeDocument({
        schemaVersion: DOCUMENT_SCHEMA_VERSION,
        documentVersion: 1,
        builderVersion: BUILDER_ENGINE_VERSION,
        metadata: {
            id: null,
            eventId: null,
            name: "Documento sin título",
            status: "draft",
            createdAt: now,
            updatedAt: now,
            ...(overrides.metadata || {}),
        },
        theme: overrides.theme || {},
        assets: overrides.assets || [],
        globals: overrides.globals || {},
        canvases: overrides.canvases || [],
        ...overrides,
    });
}

export function normalizeDocument(raw = {}) {
    const source = isObject(raw) ? raw : {};
    const now = new Date().toISOString();
    const metadata = isObject(source.metadata) ? source.metadata : {};

    return {
        schemaVersion: DOCUMENT_SCHEMA_VERSION,
        documentVersion: positiveInteger(source.documentVersion, 1),
        builderVersion: String(source.builderVersion || BUILDER_ENGINE_VERSION),
        metadata: {
            id: metadata.id ?? null,
            eventId: metadata.eventId ?? null,
            name: String(metadata.name || "Documento sin título"),
            status: String(metadata.status || "draft"),
            createdAt: String(metadata.createdAt || now),
            updatedAt: String(metadata.updatedAt || now),
        },
        theme: cloneObject(source.theme),
        assets: Array.isArray(source.assets) ? clone(source.assets) : [],
        globals: cloneObject(source.globals),
        canvases: Array.isArray(source.canvases) ? clone(source.canvases) : [],
    };
}

export function validateDocument(document) {
    const errors = [];
    if (!isObject(document)) return { valid: false, errors: ["El documento debe ser un objeto."] };
    if (document.schemaVersion !== DOCUMENT_SCHEMA_VERSION) {
        errors.push(`schemaVersion debe ser ${DOCUMENT_SCHEMA_VERSION}.`);
    }
    if (!isObject(document.metadata)) errors.push("metadata es obligatorio.");
    if (!isObject(document.theme)) errors.push("theme debe ser un objeto.");
    if (!Array.isArray(document.assets)) errors.push("assets debe ser un arreglo.");
    if (!isObject(document.globals)) errors.push("globals debe ser un objeto.");
    if (!Array.isArray(document.canvases)) errors.push("canvases debe ser un arreglo.");
    return { valid: errors.length === 0, errors };
}

function positiveInteger(value, fallback) {
    const parsed = Number(value);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}
function isObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
function cloneObject(value) {
    return isObject(value) ? clone(value) : {};
}
function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
