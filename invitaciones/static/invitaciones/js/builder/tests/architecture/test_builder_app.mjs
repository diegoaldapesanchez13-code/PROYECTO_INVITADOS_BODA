import assert from "node:assert/strict";
import { BuilderApp } from "../../app/builder_app.js";
import { createBuilderDocument } from "../../document/schema.js";

let saved = null;
const app = await BuilderApp.start({
    backend: "django",
    eventId: 7,
    document: createBuilderDocument(),
    endpoints: {
        async saveDocument(document) {
            saved = document;
            return { ok: true, document };
        },
    },
});
assert.equal(app.isStarted, true);
assert.equal(app.getDocument().metadata.eventId, 7);
await app.save();
assert.ok(saved);
assert.equal(app.isDirty, false);
await app.destroy();
assert.equal(app.isStarted, false);
console.log("test_builder_app: ok");
