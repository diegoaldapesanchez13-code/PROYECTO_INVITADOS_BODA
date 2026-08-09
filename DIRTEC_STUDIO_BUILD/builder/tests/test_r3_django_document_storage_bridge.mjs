import assert from "node:assert/strict";

import {
    DjangoDocumentStorageBridge,
} from "../integrations/django/document_storage_bridge.js";

const events = [];

globalThis.CustomEvent = class CustomEvent {
    constructor(type, options = {}) {
        this.type = type;
        this.detail = options.detail || {};
    }
};

globalThis.dispatchEvent = (event) => {
    events.push(event);
};

function response(status, payload) {
    return {
        ok: status >= 200 && status < 300,
        status,
        async json() {
            return payload;
        },
    };
}

function createBridge(revision = 10) {
    return new DjangoDocumentStorageBridge({
        initialDocument: { id: "initial" },
        revision,
        endpoint: "/document",
        publishEndpoint: "/publish",
        csrfToken: "csrf",
    });
}

{
    const requests = [];
    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        requests.push(body);
        return response(200, {
            ok: true,
            revision: body.baseRevision + 1,
        });
    };

    const bridge = createBridge(5);
    bridge.setItem("doc", JSON.stringify({ id: "first" }));
    await bridge.flush();

    bridge.setItem("doc", JSON.stringify({ id: "second" }));
    await bridge.flush();

    assert.equal(requests.length, 2);
    assert.equal(requests[0].baseRevision, 5);
    assert.equal(requests[1].baseRevision, 6);
    assert.equal(bridge.revision, 7);
}

{
    const requests = [];
    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        requests.push(body);
        return response(409, {
            ok: false,
            revision: 12,
            error: "El documento cambió en otra sesión.",
        });
    };

    const bridge = createBridge(4);
    bridge.setItem("doc", JSON.stringify({ id: "stale" }));

    await assert.rejects(
        () => bridge.flush(),
        /otra sesión/
    );

    assert.equal(requests.length, 1);
    assert.equal(requests[0].baseRevision, 4);
    assert.equal(bridge.revision, 4);
}

{
    const requests = [];
    let releaseFirst;
    const firstSave = new Promise((resolve) => {
        releaseFirst = resolve;
    });

    globalThis.fetch = async (_url, options) => {
        const body = JSON.parse(options.body);
        requests.push(body);

        if (requests.length === 1) {
            await firstSave;
        }

        return response(200, {
            ok: true,
            revision: body.baseRevision + 1,
        });
    };

    const bridge = createBridge(20);
    bridge.setItem("doc", JSON.stringify({ id: "parallel-a" }));
    const firstFlush = bridge.flush();

    bridge.setItem("doc", JSON.stringify({ id: "parallel-b" }));
    releaseFirst();
    await firstFlush;
    await bridge.flush();

    assert.equal(requests.length, 2);
    assert.equal(requests[0].baseRevision, 20);
    assert.equal(requests[0].document.id, "parallel-a");
    assert.equal(requests[1].baseRevision, 21);
    assert.equal(requests[1].document.id, "parallel-b");
    assert.equal(bridge.revision, 22);
}

console.log("DjangoDocumentStorageBridge revision tests: OK");
