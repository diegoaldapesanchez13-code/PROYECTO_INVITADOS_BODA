import { ComponentsModule } from "../../components/index.js";
import {
    COMPONENT_LIBRARY_ITEMS,
    componentInsertOptions,
    renderComponentLibrary,
    renderLayersTree,
    renderNodeInspector,
} from "../../workspace/index.js";

waitForBuilder().then(mount).catch((error) => {
    console.error("No se pudo montar la biblioteca de componentes.", error);
});

async function waitForBuilder() {
    const timeoutAt = Date.now() + 12000;
    while (!window.DIRTEC_BUILDER) {
        if (Date.now() > timeoutAt) {
            throw new Error("DIRTEC_BUILDER no estuvo disponible a tiempo.");
        }
        await new Promise((resolve) => setTimeout(resolve, 80));
    }
    return window.DIRTEC_BUILDER;
}

function mount(builder) {
    const root = document.querySelector("[data-builder-engine-root]");
    const libraryContainer = root?.querySelector("[data-engine-component-library]");
    const layersPanel = root?.querySelector("[data-engine-layers-panel]");
    const inspectorPanel = root?.querySelector("[data-engine-node-inspector]");
    const activeCanvas = root?.querySelector("[data-engine-active-canvas]");

    if (!root || !libraryContainer) return;

    const componentsModule = new ComponentsModule();
    componentsModule.start({ app: builder.app });

    let query = "";

    const renderLibrary = () => {
        renderComponentLibrary(libraryContainer, { query });
    };

    const selectInsertedNode = (node) => {
        builder.nodeWorkspace.select(node.id);

        const selectedCanvas = builder.canvasWorkspace.getSelected();
        renderLayersTree(
            layersPanel,
            selectedCanvas?.nodes || [],
            { selectedId: node.id },
        );
        renderNodeInspector(inspectorPanel, node);

        for (const element of activeCanvas?.querySelectorAll(".engine-preview-node.is-selected") || []) {
            element.classList.remove("is-selected");
        }

        const nodeElement = activeCanvas?.querySelector(
            `.engine-preview-node[data-node-id="${escapeCss(node.id)}"]`
        );
        nodeElement?.classList.add("is-selected");

        window.DIRTEC_BUILDER_TRANSFORM?.refreshOverlay?.();
    };

    const insertItem = (itemId, position = null) => {
        const item = COMPONENT_LIBRARY_ITEMS.find((entry) => entry.id === itemId);
        if (!item) throw new Error(`Componente no encontrado: ${itemId}`);

        const canvas = builder.canvasWorkspace.getSelected();
        if (!canvas) throw new Error("Selecciona o crea un lienzo primero.");

        const prepared = componentInsertOptions(item, canvas, {
            position,
            device: normalizeDevice(builder.workspace.value.previewDevice),
        });

        const node = componentsModule.service.insert(
            canvas.id,
            prepared.typeOrBlueprint,
            prepared.options,
        );

        selectInsertedNode(node);
        return node;
    };

    libraryContainer.addEventListener("input", (event) => {
        if (!event.target.matches("[data-component-library-search]")) return;
        query = event.target.value;
        renderLibrary();
        const search = libraryContainer.querySelector("[data-component-library-search]");
        search?.focus();
        search?.setSelectionRange(query.length, query.length);
    });

    libraryContainer.addEventListener("click", (event) => {
        const button = event.target.closest("[data-component-library-item]");
        if (!button) return;

        try {
            insertItem(button.dataset.componentLibraryItem);
        } catch (error) {
            window.alert(error.message || "No fue posible agregar el componente.");
        }
    });

    libraryContainer.addEventListener("dragstart", (event) => {
        const button = event.target.closest("[data-component-library-item]");
        if (!button || !event.dataTransfer) return;
        event.dataTransfer.effectAllowed = "copy";
        event.dataTransfer.setData(
            "application/x-dirtec-component",
            button.dataset.componentLibraryItem,
        );
    });

    activeCanvas?.addEventListener("dragover", (event) => {
        if (!event.dataTransfer?.types.includes("application/x-dirtec-component")) return;
        event.preventDefault();
        event.dataTransfer.dropEffect = "copy";
    });

    activeCanvas?.addEventListener("drop", (event) => {
        const itemId = event.dataTransfer?.getData("application/x-dirtec-component");
        if (!itemId) return;
        event.preventDefault();

        const liveCanvas = event.target.closest(".engine-live-canvas")
            || activeCanvas.querySelector(".engine-live-canvas");
        if (!liveCanvas) return;

        const rect = liveCanvas.getBoundingClientRect();
        const position = {
            x: ((event.clientX - rect.left) / rect.width) * 100,
            y: ((event.clientY - rect.top) / rect.height) * 100,
        };

        try {
            insertItem(itemId, position);
        } catch (error) {
            window.alert(error.message || "No fue posible agregar el componente.");
        }
    });

    renderLibrary();

    window.DIRTEC_BUILDER_COMPONENTS = Object.freeze({
        module: componentsModule,
        service: componentsModule.service,
        insert: insertItem,
        items: COMPONENT_LIBRARY_ITEMS,
    });
}

function normalizeDevice(value) {
    const key = String(value || "").toLowerCase();
    if (key.includes("tablet")) return "tablet";
    if (key.includes("desktop")) return "desktop";
    return "mobile";
}

function escapeCss(value) {
    return globalThis.CSS?.escape
        ? CSS.escape(value)
        : String(value).replaceAll('"', '\\"');
}
