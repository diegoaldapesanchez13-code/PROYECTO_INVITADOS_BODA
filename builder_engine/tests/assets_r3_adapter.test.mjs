import assert from "node:assert/strict";
import test from "node:test";
import { engineAssetToR3, r3AssetToEngine } from "../frontend/assets/index.js";

test("adaptador R3 conserva identidad, URL y metadatos", () => {
    const engine = r3AssetToEngine({ id: 9, title: "Video", url: "/media/v.mp4", mimeType: "video/mp4", metadata: { duration: 8 } });
    assert.equal(engine.id, "9");
    assert.equal(engine.type, "VIDEO");
    assert.equal(engine.duration, 8);
    const r3 = engineAssetToR3(engine);
    assert.equal(r3.url, "/media/v.mp4");
    assert.equal(r3.metadata.duration, 8);
});
