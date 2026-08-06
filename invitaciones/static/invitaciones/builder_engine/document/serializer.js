import { normalizeDocument, validateDocument } from "./schema.js";

export function serializeDocument(document, spacing = 0) {
    const normalized = normalizeDocument(document);
    const validation = validateDocument(normalized);
    if (!validation.valid) throw new Error(validation.errors.join("\n"));
    return JSON.stringify(normalized, null, spacing);
}

export function deserializeDocument(serialized) {
    if (typeof serialized !== "string") throw new TypeError("El documento serializado debe ser texto JSON.");
    return normalizeDocument(JSON.parse(serialized));
}
