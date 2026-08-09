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
    schemaVersion: 4,
    page: {
        id: "page",
        name: "Demo",
        type: "PAGE",
        settings: {},
    },
    canvases: [
        {
            id: "canvas-1",
            type: "CANVAS",
            name: "Canvas",
            parentId: null,
            canvasId: "canvas-1",
            order: 0,
            visible: true,
            locked: false,
            layoutMode: "FLOW",
            coordinateSpace: "CANVAS",
            x: 50,
            y: 50,
            width: 100,
            height: 844,
            minHeight: 0,
            maxHeight: 0,
            rotation: 0,
            scale: 1,
            opacity: 1,
            zIndex: 20,
            style: {},
            content: {},
            interaction: {
                enabled: false,
                trigger: "CLICK",
                action: { type: "NONE", value: "", target: "", options: {} },
            },
            responsive: {},
            children: ["card-1"],
        },
    ],
    nodes: [
        {
            id: "card-1",
            type: "CARD",
            name: "Card",
            parentId: "canvas-1",
            canvasId: "canvas-1",
            order: 0,
            visible: true,
            locked: false,
            layoutMode: "ABSOLUTE",
            coordinateSpace: "CANVAS",
            x: 50,
            y: 62,
            width: 40,
            height: 20,
            minHeight: 0,
            maxHeight: 0,
            rotation: 0,
            scale: 1,
            opacity: 1,
            zIndex: 20,
            style: {},
            content: {},
            interaction: {
                enabled: false,
                trigger: "CLICK",
                action: { type: "NONE", value: "", target: "", options: {} },
            },
            responsive: {},
            children: [],
        },
    ],
    assets: [],
    responsive: {
        baseDevice: "mobile",
        inheritance: {
            tablet: "mobile",
            desktop: "tablet",
        },
    },
    meta: { sourceSchemaVersion: null, migratedAt: null },
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

let flushSaves = 0;
let flushedDocument = null;
const flushListeners = new Set();
const flushController =
    connectDocumentPersistence({
        state: {
            subscribe(listener) {
                flushListeners.add(listener);
                return () => flushListeners.delete(listener);
            },
        },
        storage: {
            save(document) {
                flushSaves += 1;
                flushedDocument = document;
                return true;
            },
        },
        debounceMs: 50,
    });

flushController.flush();
assert.equal(flushSaves, 0);

for (const listener of flushListeners) {
    listener({
        type: "node:update",
        document: {
            id: "pending-document",
        },
    });
}

flushController.flush();
assert.equal(flushSaves, 1);
assert.equal(flushedDocument.id, "pending-document");

console.log(
    "R3.07.2 document persistence tests: OK"
);
