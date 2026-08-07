import assert from "node:assert/strict";
import test from "node:test";
import { AssetManagerService } from "../frontend/asset_manager/index.js";

test("carga y normaliza assets", async () => {
    const service = new AssetManagerService({
        endpoint: "/assets/",
        fetchImpl: async () => ({
            ok: true,
            status: 200,
            async json() {
                return {
                    ok: true,
                    assets: [{
                        id: 4,
                        backendId: 4,
                        type: "IMAGE",
                        category: "DECORACION",
                        name: "Foto",
                        url: "/media/foto.png",
                        size: 1200,
                    }],
                };
            },
        }),
    });

    const assets = await service.load();
    assert.equal(assets.length, 1);
    assert.equal(assets[0].id, "4");
    assert.equal(assets[0].url, "/media/foto.png");
});

test("filtra por tipo y texto", async () => {
    const service = new AssetManagerService({
        endpoint: "/assets/",
        fetchImpl: async () => ({
            ok: true,
            status: 200,
            async json() {
                return {
                    ok: true,
                    assets: [
                        { id: 1, type: "IMAGE", category: "PORTADA", name: "Portada", url: "/a.png" },
                        { id: 2, type: "VIDEO", category: "VIDEO", name: "Entrada", url: "/b.mp4" },
                    ],
                };
            },
        }),
    });

    await service.load();
    assert.equal(service.filtered({ type: "VIDEO" }).length, 1);
    assert.equal(service.filtered({ query: "porta" })[0].name, "Portada");
});
