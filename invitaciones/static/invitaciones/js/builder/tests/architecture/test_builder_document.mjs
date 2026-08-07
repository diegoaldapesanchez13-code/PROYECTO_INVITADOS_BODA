import assert from "node:assert/strict";
import {
    createBuilderDocument,
    normalizeBuilderDocument,
    validateBuilderDocument,
} from "../../document/schema.js";

const document = createBuilderDocument({
    metadata: { eventId: 42, name: "Boda" },
});
assert.equal(document.schemaVersion, 1);
assert.equal(document.metadata.eventId, 42);
assert.ok(document.canvasDocument);
assert.equal(validateBuilderDocument(document).valid, true);

const legacy = normalizeBuilderDocument({ canvas: document.canvasDocument });
assert.equal(legacy.schemaVersion, 1);
assert.equal(validateBuilderDocument(legacy).valid, true);
console.log("test_builder_document: ok");
