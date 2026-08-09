import assert from "node:assert/strict";

import {
    ASSET_SOURCES,
    ASSET_TYPES,
    AssetManager,
} from "../assets/asset_manager.js";

const savedUpload = {
    id: "saved-upload",
    type: ASSET_TYPES.IMAGE,
    source: ASSET_SOURCES.UPLOAD,
    name: "Foto guardada",
    category: "Fotografías",
    collection: "Mis archivos",
    url: "data:image/png;base64,test",
};

const memory = {
    value: {
        uploads: [savedUpload],
        recentIds: ["saved-upload"],
    },

    load() {
        return structuredClone(
            this.value
        );
    },

    save(value) {
        this.value =
            structuredClone(value);
        return true;
    },
};

const manager =
    new AssetManager({
        initialAssets: [
            {
                id: "builtin-1",
                type:
                    ASSET_TYPES.DECORATION,
                source:
                    ASSET_SOURCES.BUILTIN,
                name: "Rama integrada",
                category:
                    "Decoraciones",
                collection:
                    "Olivo",
                url:
                    "data:image/svg+xml,test",
            },
        ],
        storage: memory,
    });

assert.ok(
    manager.get("saved-upload"),
    "El upload guardado debe restaurarse."
);

assert.ok(
    manager.get("builtin-1"),
    "El asset integrado debe conservarse."
);

assert.equal(
    manager.list().length,
    2
);

assert.equal(
    manager.list({
        recent: true,
    })[0].id,
    "saved-upload"
);

assert.equal(
    memory.value.uploads.length,
    1,
    "El constructor no debe borrar los uploads guardados."
);

console.log(
    "R3.07.1 persistence tests: OK"
);