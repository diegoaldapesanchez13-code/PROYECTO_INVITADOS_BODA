import assert from "node:assert/strict";
import { DjangoDocumentAdapter } from "../../integrations/django/adapters/document_adapter.js";
import { DjangoAssetAdapter } from "../../integrations/django/adapters/asset_adapter.js";

const documentAdapter = new DjangoDocumentAdapter();
const document = documentAdapter.fromBackend({ configuracion_borrador: {} });
assert.equal(document.schemaVersion, 1);
const payload = documentAdapter.toBackend(document);
assert.equal(payload.schemaVersion, 1);
assert.ok(payload.document.documentVersion >= 2);

const asset = new DjangoAssetAdapter().fromBackend({
    id: 5,
    titulo: "Video",
    archivo_url: "/media/video.mp4",
    mime: "video/mp4",
});
assert.equal(asset.id, "5");
assert.equal(asset.type, "video");
console.log("test_django_adapters: ok");
