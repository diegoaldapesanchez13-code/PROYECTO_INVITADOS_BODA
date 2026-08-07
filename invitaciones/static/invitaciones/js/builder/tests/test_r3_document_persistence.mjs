import assert from "node:assert/strict";

import {
    BuilderDocumentStorage,
    connectDocumentPersistence,
} from "../persistence/document_storage.js";

const memory = {
    value: null,

    getItem() {
        return this.value;
    },

    setItem(key, value) {
        this.value = value;
    },

    removeItem() {
        this.value = null;
    },
};

const storage =
    new BuilderDocumentStorage({
        key: "test",
        storage: memory,
    });

const document = {
    schemaVersion: 3,
    page: {
        name: "Demo",
    },
    sections: [
        {
            id: "section-1",
        },
    ],
    nodes: [
        {
            id: "card-1",
            x: 50,
            y: 62,
        },
    ],
    meta: {},
};

assert.equal(
    storage.save(document),
    true
);

assert.deepEqual(
    storage.load(),
    document
);

const listeners = new Set();

const state = {
    subscribe(listener) {
        listeners.add(listener);

        return () =>
            listeners.delete(listener);
    },
};

connectDocumentPersistence({
    state,
    storage,
    debounceMs: 0,
});

for (const listener of listeners) {
    listener({
        type: "node:update",
        document: {
            ...document,
            nodes: [
                {
                    id: "card-1",
                    x: 70,
                    y: 80,
                },
            ],
        },
    });
}

await new Promise(
    (resolve) =>
        setTimeout(resolve, 5)
);

assert.equal(
    storage.load().nodes[0].y,
    80
);

for (const listener of listeners) {
    listener({
        type: "selection:change",
        document: {
            invalid: true,
        },
    });
}

await new Promise(
    (resolve) =>
        setTimeout(resolve, 5)
);

assert.equal(
    storage.load().nodes[0].y,
    80
);

storage.clear();

assert.equal(
    storage.load(),
    null
);

console.log(
    "R3.07.2 document persistence tests: OK"
);