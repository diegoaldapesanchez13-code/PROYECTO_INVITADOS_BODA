import assert from "node:assert/strict";

import {
    ASSET_SOURCES,
    ASSET_TYPES,
    AssetManager,
} from "../assets/asset_manager.js";

const memory = {
    value: null,

    load() {
        return this.value;
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
                name: "Rama",
                category:
                    "Decoraciones",
                collection:
                    "Olivo",
                url:
                    "data:image/svg+xml,test",
                tags: [
                    "rama",
                    "olivo",
                ],
            },
        ],
        storage: memory,
    });

const upload =
    manager.register({
        id: "upload-1",
        type:
            ASSET_TYPES.IMAGE,
        source:
            ASSET_SOURCES.UPLOAD,
        name: "Foto",
        category:
            "Fotografías",
        collection:
            "Mis archivos",
        url:
            "data:image/png,test",
    });

assert.equal(
    manager.list().length,
    2
);

assert.equal(
    manager.list({
        source:
            ASSET_SOURCES.UPLOAD,
    }).length,
    1
);

assert.equal(
    manager.list({
        query: "olivo",
    })[0].id,
    "builtin-1"
);

manager.use("upload-1");

assert.equal(
    manager.list({
        recent: true,
    })[0].id,
    "upload-1"
);

manager.toggleFavorite(
    "upload-1"
);

assert.equal(
    manager.list({
        favorite: true,
    })[0].favorite,
    true
);

assert.equal(
    memory.value.uploads.length,
    1
);

assert.equal(
    manager.remove(
        upload.id
    ),
    true
);

assert.throws(
    () =>
        manager.remove(
            "builtin-1"
        )
);

console.log(
    "R3.07 Asset Studio Core tests: OK"
);
