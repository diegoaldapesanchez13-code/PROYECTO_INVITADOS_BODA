import {
    DjangoDocumentStorageBridge,
    persistenceEventName,
} from "./document_storage_bridge.js";

import {
    DjangoAssetAdapter,
} from "./asset_adapter.js";

const root = document.getElementById("dirtec-builder-bootstrap");

if (!root) {
    throw new Error("No existe bootstrap de DIRTEC Builder.");
}

const config = JSON.parse(root.textContent || "{}");

const bridge = new DjangoDocumentStorageBridge({
    initialDocument: config.initialDocument || null,
    revision: config.revision || 0,
    endpoint: config.endpoints.document,
    publishEndpoint: config.endpoints.publish,
    csrfToken: config.csrfToken,
});

globalThis.__DIRTEC_BUILDER_DOCUMENT_STORAGE__ = bridge;
globalThis.__DIRTEC_BUILDER_BOOTSTRAP__ = config;

const assetAdapter = new DjangoAssetAdapter({
    listEndpoint: config.endpoints.assets,
    deleteEndpointTemplate:
        config.endpoints.assetDeleteTemplate,
    csrfToken: config.csrfToken,
});

globalThis.__DIRTEC_BUILDER_INITIAL_ASSETS__ =
    Array.isArray(config.initialAssets)
        ? config.initialAssets
        : [];

globalThis.__DIRTEC_BUILDER_ASSET_STORAGE__ = null;
globalThis.__DIRTEC_BUILDER_ASSET_UPLOADER__ =
    (file) => assetAdapter.upload(file);
globalThis.__DIRTEC_BUILDER_ASSET_DELETER__ =
    (assetId) => assetAdapter.remove(assetId);

const status = document.querySelector("[data-dirtec-save-status]");
const publishButton = document.querySelector("[data-dirtec-publish]");

globalThis.addEventListener(
    persistenceEventName(),
    (event) => {
        if (!status) return;
        const detail = event.detail || {};
        status.textContent = detail.message || detail.state || "";
        status.dataset.state = detail.state || "";
        status.title = `Revisión ${detail.revision ?? bridge.revision}`;
    },
);

function markConnectedIfIdle() {
    if (!status || status.dataset.state !== "ready") {
        return;
    }

    status.textContent = "Conectado";
    status.title = `Revision ${bridge.revision}`;
}

publishButton?.addEventListener("click", async () => {
    publishButton.disabled = true;
    try {
        await bridge.publish();
    } catch (error) {
        console.error(error);
    } finally {
        publishButton.disabled = false;
    }
});

await import("../../demo_r3_07.js" + "?v=phase-f3-target-selection");
markConnectedIfIdle();
