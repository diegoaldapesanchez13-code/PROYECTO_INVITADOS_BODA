import {
    migrateDocumentToV4,
    normalizeDocumentV4,
    validateDocumentV4,
} from "./schema_v4.js?v=phase-f3-canvas-contract";

export function canonicalizeDocumentV4(document) {
    const canonical =
        Number(document?.schemaVersion) === 4
            ? normalizeDocumentV4(document)
            : migrateDocumentToV4(document || {});

    const validation = validateDocumentV4(canonical);

    if (!validation.valid) {
        throw new Error(validation.errors.join("\n"));
    }

    return canonical;
}
