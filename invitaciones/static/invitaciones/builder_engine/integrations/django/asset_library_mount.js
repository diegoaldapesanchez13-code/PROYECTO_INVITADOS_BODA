import {
    AssetManagerService,
    renderAssetLibrary,
} from "../../asset_manager/index.js";

waitForBuilder().then(mount).catch((error) => {
    console.error("No se pudo montar la biblioteca de assets.", error);
});

async function waitForBuilder() {
    const timeoutAt = Date.now() + 12000;
    while (!window.DIRTEC_BUILDER) {
        if (Date.now() > timeoutAt) throw new Error("DIRTEC_BUILDER no disponible.");
        await new Promise((resolve) => setTimeout(resolve, 80));
    }
    return window.DIRTEC_BUILDER;
}

async function mount(builder) {
    const root = document.querySelector("[data-builder-engine-root]");
    const container = root?.querySelector("[data-engine-asset-library]");
    if (!root || !container) return;

    const endpoint = builder.config?.endpoints?.assets;
    if (!endpoint) throw new Error("Falta endpoint de assets.");

    const service = new AssetManagerService({ endpoint });
    let filter = "ALL";
    let query = "";

    const render = () => {
        renderAssetLibrary(container, {
            assets: service.filtered({ type: filter, query }),
            loading: service.loading,
            error: service.error,
            type: filter,
            query,
        });
    };

    service.subscribe(render);
    await service.load();

    container.addEventListener("click", (event) => {
        const filterButton = event.target.closest("[data-asset-filter]");
        const assetButton = event.target.closest("[data-asset-id]");

        if (filterButton) {
            filter = filterButton.dataset.assetFilter;
            render();
            return;
        }

        if (!assetButton) return;

        const asset = service.find(assetButton.dataset.assetId);
        if (!asset) return;

        const node = builder.nodeWorkspace.getSelected();
        if (!node) {
            window.alert("Selecciona primero un componente Imagen o Video.");
            return;
        }

        const nodeType = String(node.type || "").toUpperCase();
        if (!["IMAGE", "VIDEO"].includes(nodeType)) {
            window.alert("El componente seleccionado no acepta archivos multimedia.");
            return;
        }

        if (nodeType === "IMAGE" && !["IMAGE", "GIF"].includes(asset.type)) {
            window.alert("Selecciona una imagen para este componente.");
            return;
        }

        if (nodeType === "VIDEO" && asset.type !== "VIDEO") {
            window.alert("Selecciona un video para este componente.");
            return;
        }

        builder.nodeWorkspace.update("content", {
            ...(node.content || {}),
            assetId: asset.id,
            backendId: asset.backendId,
            url: asset.url,
            source: asset.url,
            sourceType: "upload",
            mimeType: asset.mimeType,
            placeholder: false,
        }, {
            label: `Asignar ${asset.name}`,
            mergeKey: null,
        });
    });

    container.addEventListener("input", (event) => {
        if (!event.target.matches("[data-asset-search]")) return;
        query = event.target.value;
        render();
        const search = container.querySelector("[data-asset-search]");
        search?.focus({ preventScroll: true });
        search?.setSelectionRange(query.length, query.length);
    });

    window.DIRTEC_BUILDER_ASSETS = Object.freeze({
        service,
        reload: () => service.load(),
        select(assetId) {
            return service.find(assetId);
        },
    });
}
