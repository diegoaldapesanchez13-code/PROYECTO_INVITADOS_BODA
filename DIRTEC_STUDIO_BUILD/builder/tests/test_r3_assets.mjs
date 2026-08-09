
import assert from "node:assert/strict";

import {
    AssetManager,
    ASSET_TYPES,
} from "../assets/asset_manager.js";

const manager = new AssetManager([
    {
        id: "a1",
        type: ASSET_TYPES.DECORATION,
        name: "Rama",
        category: "Decoraciones",
        url: "data:image/svg+xml,test",
        tags: ["olivo"],
    },
]);

assert.equal(
    manager.get("a1").name,
    "Rama"
);

assert.equal(
    manager.resolve("a1"),
    "data:image/svg+xml,test"
);

assert.equal(
    manager.list({
        category: "Decoraciones",
    }).length,
    1
);

assert.equal(
    manager.list({
        query: "olivo",
    }).length,
    1
);

assert.equal(
    manager.toggleFavorite("a1")
        .favorite,
    true
);

console.log(
    "R3.06 AssetManager tests: OK"
);
