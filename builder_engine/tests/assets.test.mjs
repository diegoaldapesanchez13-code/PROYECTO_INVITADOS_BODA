import assert from "node:assert/strict";
import test from "node:test";
import { BuilderApp } from "../frontend/app/index.js";
import { createDocument, validateDocument } from "../frontend/document/index.js";
import { ASSET_TYPES, registerAssetsModule } from "../frontend/assets/index.js";

test("AssetsModule registra recursos persistentes en el Documento", async () => {
    const app = new BuilderApp({ document: createDocument() });
    const module = registerAssetsModule(app);
    await app.start();
    const asset = module.service.add({ id: "img-1", type: ASSET_TYPES.IMAGE, name: "Portada", url: "/media/editor/portada.jpg", mimeType: "image/jpeg" });
    assert.equal(asset.id, "img-1");
    assert.equal(app.getDocument().assets.length, 1);
    assert.equal(module.service.resolve("img-1"), "/media/editor/portada.jpg");
    assert.equal(app.isDirty, true);
    await app.destroy();
});

test("Documento rechaza Base64 y blob URLs", async () => {
    const app = new BuilderApp({ document: createDocument() });
    const module = registerAssetsModule(app);
    await app.start();
    assert.throws(() => module.service.add({ id: "bad", url: "data:image/png;base64,AAA" }), /temporal|Base64/);
    assert.throws(() => module.service.add({ id: "blob", url: "blob:http:\/\/localhost\/123" }), /temporal|Base64/);
    const validation = validateDocument({ ...createDocument(), assets: [{ id: "x", url: "data:image/png;base64,AAA" }] });
    assert.equal(validation.valid, false);
    await app.destroy();
});

test("AssetsModule evita eliminar recursos referenciados", async () => {
    const app = new BuilderApp({ document: createDocument({
        assets: [{ id: "img-1", type: "IMAGE", source: "UPLOAD", name: "Foto", url: "/media/foto.jpg" }],
        canvases: [{ id: "c", nodes: [{ id: "n", type: "IMAGE", content: { assetId: "img-1" } }] }],
    }) });
    const module = registerAssetsModule(app);
    await app.start();
    assert.deepEqual(module.service.references("img-1"), ["canvases[0].nodes[0].content.assetId"]);
    await assert.rejects(() => module.service.remove("img-1"), /utilizado/);
    assert.equal(await module.service.remove("img-1", { force: true, deleteRemote: false }), true);
    await app.destroy();
});

test("AssetsModule delega upload al adaptador y solo guarda metadatos", async () => {
    const fakeFile = { name: "video.mp4", type: "video/mp4", size: 999 };
    const app = new BuilderApp({ document: createDocument() });
    const module = registerAssetsModule(app, { uploader: async () => ({ id: 42, url: "/media/assets/video.mp4", mimeType: "video/mp4", type: "VIDEO" }) });
    await app.start();
    const asset = await module.service.upload(fakeFile, { category: "Videos" });
    assert.equal(asset.backendId, 42);
    assert.equal(asset.url, "/media/assets/video.mp4");
    assert.equal(JSON.stringify(app.getDocument()).includes("base64"), false);
    assert.equal(JSON.stringify(app.getDocument()).includes("blob:"), false);
    await app.destroy();
});
