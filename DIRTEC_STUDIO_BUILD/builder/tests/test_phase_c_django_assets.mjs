import assert from "node:assert/strict";
import test from "node:test";

import {
    AssetManager,
} from "../assets/asset_manager.js";
import {
    AssetUploadService,
} from "../assets/uploads.js";
import {
    parseDatabaseAssetId,
} from "../integrations/django/asset_adapter.js";

test("upload remoto registra URL persistente sin data URL", async () => {
    const manager = new AssetManager();
    const calls = [];

    const service = new AssetUploadService({
        manager,
        maxBytes: 1024,
        uploader: async (file) => {
            calls.push(file.name);
            return {
                id: "db-41",
                type: "IMAGE",
                source: "UPLOAD",
                name: "foto",
                category: "Fotografías",
                collection: "Mis archivos",
                url: "/media/editor_invitaciones/assets/foto.jpg",
                previewUrl: "/media/editor_invitaciones/assets/foto.jpg",
                mimeType: "image/jpeg",
                metadata: {
                    size: file.size,
                    persistent: true,
                },
            };
        },
    });

    const file = new File(
        [new Uint8Array([1, 2, 3])],
        "foto.jpg",
        { type: "image/jpeg" },
    );

    const asset = await service.importFile(file);

    assert.deepEqual(calls, ["foto.jpg"]);
    assert.equal(asset.id, "db-41");
    assert.equal(asset.url.startsWith("data:"), false);
    assert.equal(
        asset.url,
        "/media/editor_invitaciones/assets/foto.jpg",
    );
});

test("delete remoto delega al adapter", async () => {
    const manager = new AssetManager();
    let deleted = null;

    const service = new AssetUploadService({
        manager,
        deleter: async (assetId) => {
            deleted = assetId;
            return { ok: true };
        },
    });

    const result = await service.removeAsset("db-9");
    assert.equal(deleted, "db-9");
    assert.equal(result.ok, true);
});

test("id persistente se traduce a PK Django", () => {
    assert.equal(parseDatabaseAssetId("db-123"), "123");
    assert.equal(parseDatabaseAssetId("asset-demo"), null);
});
