import {
    createBuilderDocument,
    normalizeBuilderDocument,
    touchBuilderDocument,
} from "../../../document/schema.js";

export class DjangoDocumentAdapter {
    fromBackend(payload = {}) {
        const source = payload.document
            || payload.configuracion_borrador
            || payload.configuration
            || payload;

        if (!source || typeof source !== "object" || Array.isArray(source)) {
            return createBuilderDocument();
        }

        return normalizeBuilderDocument(source);
    }

    toBackend(document) {
        const normalized = touchBuilderDocument(document);
        return {
            document: normalized,
            schemaVersion: normalized.schemaVersion,
            documentVersion: normalized.documentVersion,
        };
    }
}
