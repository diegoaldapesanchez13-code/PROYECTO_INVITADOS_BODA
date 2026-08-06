import {
    createEmptyDocument as createCanvasDocument,
    normalizeDocument as normalizeCanvasDocument,
    validateDocument as validateCanvasDocument,
} from "../core/schema.js";

export const DOCUMENT_SCHEMA_VERSION = 1;
export const BUILDER_VERSION = "0.6.1";

const clone = (value) => {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }
    return JSON.parse(JSON.stringify(value));
};

export function createBuilderDocument(overrides = {}) {
    const now = new Date().toISOString();
    const canvasSource = overrides.canvasDocument || overrides.canvas || null;

    return normalizeBuilderDocument({
        schemaVersion: DOCUMENT_SCHEMA_VERSION,
        documentVersion: 1,
        builderVersion: BUILDER_VERSION,
        metadata: {
            id: null,
            eventId: null,
            name: "Documento sin título",
            status: "draft",
            createdAt: now,
            updatedAt: now,
            ...(overrides.metadata || {}),
        },
        theme: clone(overrides.theme || {}),
        assets: Array.isArray(overrides.assets) ? clone(overrides.assets) : [],
        globals: clone(overrides.globals || {}),
        canvasDocument: canvasSource || createCanvasDocument(),
    });
}

export function normalizeBuilderDocument(raw = {}) {
    const source = raw && typeof raw === "object" ? raw : {};
    const now = new Date().toISOString();
    const metadata = source.metadata && typeof source.metadata === "object"
        ? source.metadata
        : {};

    const document = {
        schemaVersion: DOCUMENT_SCHEMA_VERSION,
        documentVersion: positiveInteger(source.documentVersion, 1),
        builderVersion: String(source.builderVersion || BUILDER_VERSION),
        metadata: {
            id: metadata.id ?? null,
            eventId: metadata.eventId ?? null,
            name: String(metadata.name || "Documento sin título"),
            status: String(metadata.status || "draft"),
            createdAt: String(metadata.createdAt || now),
            updatedAt: String(metadata.updatedAt || now),
        },
        theme: plainObject(source.theme),
        assets: Array.isArray(source.assets) ? clone(source.assets) : [],
        globals: plainObject(source.globals),
        canvasDocument: normalizeCanvasDocument(
            source.canvasDocument || source.canvas || createCanvasDocument()
        ),
    };

    return document;
}

export function validateBuilderDocument(document) {
    const errors = [];

    if (!document || typeof document !== "object") {
        return { valid: false, errors: ["El documento debe ser un objeto."] };
    }
    if (document.schemaVersion !== DOCUMENT_SCHEMA_VERSION) {
        errors.push(`schemaVersion debe ser ${DOCUMENT_SCHEMA_VERSION}.`);
    }
    if (!document.metadata || typeof document.metadata !== "object") {
        errors.push("metadata es obligatorio.");
    }
    if (!Array.isArray(document.assets)) {
        errors.push("assets debe ser un arreglo.");
    }

    const canvasValidation = validateCanvasDocument(document.canvasDocument);
    errors.push(...canvasValidation.errors.map((error) => `canvasDocument: ${error}`));

    return { valid: errors.length === 0, errors };
}

export function serializeBuilderDocument(document, spacing = 0) {
    const normalized = normalizeBuilderDocument(document);
    const validation = validateBuilderDocument(normalized);
    if (!validation.valid) {
        throw new Error(validation.errors.join("\n"));
    }
    return JSON.stringify(normalized, null, spacing);
}

export function touchBuilderDocument(document) {
    const normalized = normalizeBuilderDocument(document);
    normalized.documentVersion += 1;
    normalized.metadata.updatedAt = new Date().toISOString();
    return normalized;
}

function positiveInteger(value, fallback) {
    const number = Number(value);
    return Number.isInteger(number) && number > 0 ? number : fallback;
}

function plainObject(value) {
    return value && typeof value === "object" && !Array.isArray(value)
        ? clone(value)
        : {};
}
