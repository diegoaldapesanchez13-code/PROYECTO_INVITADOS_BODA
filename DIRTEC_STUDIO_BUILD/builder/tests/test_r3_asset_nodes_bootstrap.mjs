import assert from "node:assert/strict";

import {
    useAsset,
} from "../assets/asset_nodes.js";

import {
    ASSET_TYPES,
} from "../assets/asset_manager.js";

assert.throws(
    () => useAsset({
        state: {
            document: {
                nodes: [],
            },
            getNode() {
                return null;
            },
        },
        asset: {
            id: "image-1",
            type: ASSET_TYPES.IMAGE,
            name: "Imagen",
            url: "https://example.com/image.jpg",
        },
    }),
    /No existe un lienzo o contenedor destino/,
);

console.log("Asset nodes bootstrap test: OK");
