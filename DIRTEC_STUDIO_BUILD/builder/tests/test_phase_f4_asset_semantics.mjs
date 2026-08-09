import assert from "node:assert/strict";
import test from "node:test";

import {
    ASSET_TYPES,
    AssetManager,
    normalizeAsset,
} from "../assets/asset_manager.js";

import {
    AssetUploadService,
    typeFromMime,
} from "../assets/uploads.js";

test("F.4 image formats are media IMAGE, not semantic DECORATION", () => {
    for (const mime of [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/svg+xml",
    ]) {
        assert.equal(typeFromMime(mime), ASSET_TYPES.IMAGE);
    }

    assert.equal(typeFromMime("video/mp4"), ASSET_TYPES.VIDEO);
});

test("F.4 local image uploads preserve alpha and GIF animation metadata", async () => {
    const previousImage = globalThis.Image;
    const previousFileReader = globalThis.FileReader;

    globalThis.Image = class FakeImage {
        naturalWidth = 160;
        naturalHeight = 80;
        #listeners = new Map();

        addEventListener(type, listener) {
            this.#listeners.set(type, listener);
        }

        set src(_value) {
            queueMicrotask(() => this.#listeners.get("load")?.());
        }
    };

    globalThis.FileReader = class FakeFileReader {
        result = "";
        #listeners = new Map();

        addEventListener(type, listener) {
            this.#listeners.set(type, listener);
        }

        readAsDataURL(file) {
            this.result = `data:${file.type};base64,dGVzdA==`;
            queueMicrotask(() => this.#listeners.get("load")?.());
        }
    };

    try {
        const manager = new AssetManager();
        const service = new AssetUploadService({ manager });
        const cases = [
            ["alpha.png", "image/png", false],
            ["alpha.webp", "image/webp", false],
            ["animado.gif", "image/gif", true],
        ];

        for (const [name, mime, animated] of cases) {
            const asset = await service.importFile(
                new File(
                    [new Uint8Array([1, 2, 3])],
                    name,
                    { type: mime },
                ),
            );

            assert.equal(asset.type, ASSET_TYPES.IMAGE);
            assert.notEqual(asset.type, ASSET_TYPES.DECORATION);
            assert.equal(asset.metadata.mediaKind, "IMAGE");
            assert.equal(asset.metadata.supportsAlpha, true);
            assert.equal(asset.metadata.animated, animated);
        }
    } finally {
        globalThis.Image = previousImage;
        globalThis.FileReader = previousFileReader;
    }
});

test("F.4 normalized GIF assets keep image media semantics", () => {
    const asset = normalizeAsset({
        id: "gif-1",
        type: ASSET_TYPES.IMAGE,
        url: "/media/animado.gif",
        metadata: {
            animated: true,
            supportsAlpha: true,
            mediaKind: "IMAGE",
        },
    });

    assert.equal(asset.mimeType, "image/gif");
    assert.equal(asset.type, ASSET_TYPES.IMAGE);
    assert.equal(asset.metadata.animated, true);
    assert.equal(asset.metadata.mediaKind, "IMAGE");
});
