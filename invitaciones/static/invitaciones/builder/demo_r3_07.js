import {
    BuilderState,
    COORDINATE_SPACES,
    LAYOUT_MODES,
    NODE_TYPES,
    createEmptyDocument,
} from "./core/index.js?v=f4-native-v4-freeze";

import {
    UniversalRenderer,
} from "./renderer/renderer.js";

import {
    CanvasSelectionEngine,
} from "./canvas/selection.js";

import {
    CanvasManager,
} from "./canvas/canvas_manager.js?v=f4-native-v4-freeze";

import {
    UniversalInspector,
} from "./inspector/index.js?v=f4-native-v4-freeze";

import {
    AutoLayoutEngine,
} from "./layout/auto_layout.js?v=f4-native-v4-freeze";

import {
    AssetManager,
} from "./assets/asset_manager.js";

import {
    AssetStorage,
} from "./assets/storage.js";

import {
    BuilderDocumentStorage,
    connectDocumentPersistence,
} from "./persistence/document_storage.js?v=f4-native-v4-freeze";

import {
    AssetUploadService,
} from "./assets/uploads.js";

import {
    createStarterAssetCatalog,
} from "./assets/catalog.js";

import {
    AssetLibrary,
} from "./assets/library.js";

import {
    useAsset,
} from "./assets/asset_nodes.js?v=f4-native-v4-freeze";

import {
    LayerTree,
} from "./layers/layer_tree.js?v=f4-native-v4-freeze";

import {
    ComponentLibrary,
} from "./components/index.js?v=f4-native-v4-freeze";

import { MobilePreview } from "./preview/mobile_preview.js";
import { ExperiencePanel } from "./experience/panel.js";

const assetStorage =
    globalThis.__DIRTEC_BUILDER_ASSET_STORAGE__
    === undefined
        ? new AssetStorage({
            key:
                "dirtec.builder.r3.assets",
        })
        : globalThis
            .__DIRTEC_BUILDER_ASSET_STORAGE__;

const persistentAssets =
    Array.isArray(
        globalThis
            .__DIRTEC_BUILDER_INITIAL_ASSETS__
    )
        ? globalThis
            .__DIRTEC_BUILDER_INITIAL_ASSETS__
        : [];

const assets =
    new AssetManager({
        initialAssets: [
            ...createStarterAssetCatalog(),
            ...persistentAssets,
        ],
        storage:
            assetStorage,
    });

const uploadService =
    new AssetUploadService({
        manager: assets,
        maxBytes:
            80 * 1024 * 1024,
        uploader:
            globalThis
                .__DIRTEC_BUILDER_ASSET_UPLOADER__
            || null,
        deleter:
            globalThis
                .__DIRTEC_BUILDER_ASSET_DELETER__
            || null,
    });

const djangoDocumentStorage =
    globalThis
        .__DIRTEC_BUILDER_DOCUMENT_STORAGE__
    || null;

const documentStorage =
    new BuilderDocumentStorage({
        key:
            "dirtec.builder.r3.document",
        storage:
            djangoDocumentStorage
            || globalThis.localStorage,
        canonicalV4: true,
    });

const savedDocument =
    documentStorage.load();

const state =
    new BuilderState(
        savedDocument
        || createEmptyDocument({
            page: {
                name:
                    "Portada Olivo Premium",
            },
        })
    );

let canvasNode;

if (!savedDocument) {
canvasNode = state.createNode(
    NODE_TYPES.CANVAS,
    {
        name: "Portada",
        minHeight: 900,
        height: "auto",
        style: {
            paddingX: 24,
            paddingY: 30,
            overflow: "hidden",
            direction: "column",
            align: "center",
            justify: "center",
            gap: 18,
            sizingX: "fixed",
            sizingY: "fixed",
            backgroundColor: "#f7f2e8",
        },
    }
);

useAsset({
    state,
    asset:
        assets.get(
            "bg-olive-watercolor"
        ),
    selectedNodeId: canvasNode.id,
});

const frame = useAsset({
    state,
    asset:
        assets.get("dec-gold-frame"),
    selectedNodeId: canvasNode.id,
    position: {
        x: 50,
        y: 50,
    },
});

state.updateNode(
    frame.id,
    {
        width: 92,
        height: 92,
        zIndex: 4,
        locked: true,
    },
    {
        ignoreLock: true,
    }
);

const leftBranch = useAsset({
    state,
    asset:
        assets.get(
            "dec-olive-corner-left"
        ),
    selectedNodeId: canvasNode.id,
    position: {
        x: 13,
        y: 19,
    },
});

state.updateNode(
    leftBranch.id,
    {
        width: 42,
        height: 42,
        rotation: -5,
        zIndex: 5,
    }
);

const rightBranch = useAsset({
    state,
    asset:
        assets.get(
            "dec-olive-corner-right"
        ),
    selectedNodeId: canvasNode.id,
    position: {
        x: 87,
        y: 81,
    },
});

state.updateNode(
    rightBranch.id,
    {
        width: 42,
        height: 42,
        rotation: 4,
        zIndex: 5,
    }
);

const contentCard = state.createNode(
    NODE_TYPES.CARD,
    {
        name: "Tarjeta principal",
        parentId: canvasNode.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.ABSOLUTE,
        coordinateSpace:
            COORDINATE_SPACES.CANVAS,
        x: 50,
        y: 51,
        width: 74,
        height: 58,
        zIndex: 20,
        style: {
            direction: "column",
            align: "center",
            justify: "center",
            gap: 18,
            paddingX: 34,
            paddingY: 34,
            sizingX: "fixed",
            sizingY: "fixed",
            backgroundColor:
                "rgba(255,253,248,.86)",
            borderRadius: 28,
            borderWidth: 1,
            borderColor:
                "rgba(183,154,77,.55)",
            boxShadow:
                "0 24px 70px rgba(44,54,35,.20)",
            overflow: "hidden",
        },
    }
);

useAsset({
    state,
    asset:
        assets.get("bg-ivory-paper"),
    selectedNodeId: contentCard.id,
});

const monogram = state.createNode(
    NODE_TYPES.TEXT,
    {
        name: "Monograma",
        parentId: contentCard.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.FLOW,
        width: 100,
        height: 10,
        content: {
            text: "F & D",
            tag: "p",
        },
        style: {
            sizingX: "fill",
            sizingY: "hug",
            hugHeight: 10,
            color: "#9b7c2f",
            fontFamily:
                "Georgia, serif",
            fontSize: 22,
            fontWeight: 600,
            textAlign: "center",
            letterSpacing: 5,
        },
    }
);

const names = state.createNode(
    NODE_TYPES.TEXT,
    {
        name: "Nombres",
        parentId: contentCard.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.FLOW,
        width: 100,
        height: 18,
        content: {
            text: "Fernanda & Diego",
            tag: "h1",
        },
        style: {
            sizingX: "fill",
            sizingY: "hug",
            hugHeight: 18,
            color: "#405036",
            fontFamily:
                "Georgia, serif",
            fontSize: 46,
            fontWeight: 500,
            textAlign: "center",
            lineHeight: 1.05,
        },
    }
);

const subtitle = state.createNode(
    NODE_TYPES.TEXT,
    {
        name: "Frase",
        parentId: contentCard.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.FLOW,
        width: 100,
        height: 10,
        content: {
            text:
                "Con mucha alegría queremos compartir este día contigo",
            tag: "p",
        },
        style: {
            sizingX: "fill",
            sizingY: "hug",
            hugHeight: 10,
            color: "#66705f",
            fontFamily:
                "Georgia, serif",
            fontSize: 18,
            fontWeight: 400,
            textAlign: "center",
            lineHeight: 1.45,
        },
    }
);

const divider = useAsset({
    state,
    asset:
        assets.get(
            "dec-gold-divider"
        ),
    selectedNodeId: contentCard.id,
    position: {
        x: 50,
        y: 67,
    },
});

state.updateNode(
    divider.id,
    {
        width: 68,
        height: 8,
        zIndex: 24,
    }
);

const date = state.createNode(
    NODE_TYPES.TEXT,
    {
        name: "Fecha",
        parentId: contentCard.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.FLOW,
        width: 100,
        height: 10,
        content: {
            text:
                "21 · NOVIEMBRE · 2026",
            tag: "p",
        },
        style: {
            sizingX: "fill",
            sizingY: "hug",
            hugHeight: 10,
            color: "#405036",
            fontFamily:
                "Georgia, serif",
            fontSize: 18,
            fontWeight: 600,
            textAlign: "center",
            letterSpacing: 3,
        },
    }
);

const button = state.createNode(
    NODE_TYPES.BUTTON,
    {
        name: "Botón ubicación",
        parentId: contentCard.id,
        canvasId: canvasNode.id,
        layoutMode:
            LAYOUT_MODES.FLOW,
        width: 44,
        height: 9,
        content: {
            label: "Ver ubicación",
            href: "#",
        },
        style: {
            sizingX: "hug",
            sizingY: "hug",
            hugWidth: 44,
            hugHeight: 9,
            color: "#fff",
            backgroundColor:
                "#526043",
            borderRadius: 999,
            paddingX: 24,
            paddingY: 11,
            fontFamily:
                "Arial, sans-serif",
            fontSize: 14,
            fontWeight: 700,
            boxShadow:
                "0 10px 25px rgba(54,68,45,.20)",
        },
    }
);

documentStorage.save(
    state.document
);
} else {
    canvasNode =
        state.document.canvases[0]
        || null;
}

const stopDocumentPersistence =
    connectDocumentPersistence({
        state,
        storage:
            documentStorage,
    });

const viewport =
    document.querySelector(
        "[data-r3-canvas-viewport]"
    );

const zoomLayer =
    document.querySelector(
        "[data-r3-canvas-zoom-layer]"
    );

const surface =
    document.querySelector(
        "[data-r3-canvas-surface]"
    );

const overlayLayer =
    document.querySelector(
        "[data-r3-canvas-overlay-layer]"
    );

const inspectorRoot =
    document.querySelector(
        "[data-r3-inspector]"
    );

const libraryRoot =
    document.querySelector(
        "[data-r3-library]"
    );

const layersRoot =
    document.querySelector(
        "[data-r3-layers]"
    );

const componentsRoot =
    document.querySelector(
        "[data-r3-components]"
    );

const canvasesRoot =
    document.querySelector(
        "[data-r3-canvases]"
    );

const experienceRoot =
    document.querySelector(
        "[data-r3-experience]"
    );

const status =
    document.querySelector(
        "[data-r3-status]"
    );


const builderRuntimeContext =
    globalThis.__DIRTEC_BUILDER_BOOTSTRAP__
    || {};
const eventContext =
    builderRuntimeContext.event
    || {};
const invitationContext =
    builderRuntimeContext.invitationPreview
    || {
        groupName: "Invitación de ejemplo",
        groupType: "",
        groupTypeLabel: "Vista previa",
        totalGuests: 0,
        confirmedGuests: 0,
        pendingGuests: 0,
    };

const previewRoot = document.querySelector("[data-r3-preview]");
const mobilePreview = new MobilePreview({
    root: previewRoot,
    state,
    assetResolver(assetId) { return assets.resolve(assetId); },
    invitationContext,
    eventContext,
});

document.querySelector("[data-r3-open-preview]")?.addEventListener("click", () => {
    mobilePreview.open();
});

const renderer =
    new UniversalRenderer({
        editable: true,
        device: "mobile",
        assetResolver(assetId) {
            return assets.resolve(assetId);
        },
        eventContext,
        invitationContext,
    });

renderer.mount(
    surface,
    state.document
);

let inspector;
let layers;
let canvases;
let components;
let experiencePanel;

const canvasEngine =
    new CanvasSelectionEngine({
        state,
        renderer,
        viewport,
        zoomLayer,
        surface,
        overlayLayer,

        onSelectionChange(node) {
            inspector?.setSelection(
                node?.id || null
            );

            if (node?.id) {
                layers?.reveal(node.id);
            }

            status.textContent = node
                ? `${node.type}: ${node.name}`
                : "Ningún nodo seleccionado";
        },

        onInteractionState(event) {
            if (event.active) {
                status.textContent =
                    event.mode === "resize"
                        ? "Redimensionando..."
                        : "Moviendo...";
            }

            if (event.committed) {
                inspector?.refresh();
                status.textContent =
                    "Transformación aplicada";
            }
        },
    });

const autoLayout =
    new AutoLayoutEngine({
        state,
        renderer,
        canvas: canvasEngine,
    });

inspector =
    new UniversalInspector({
        root: inspectorRoot,
        state,
        renderer,
        canvas: canvasEngine,
        assets,
        uploadService,

        onNodeUpdated() {
            autoLayout.applyAll();
            inspector.refresh();
        },

        onStatus(message) {
            status.textContent = message;
        },
    });

layers =
    new LayerTree({
        root: layersRoot,
        state,
        canvas: canvasEngine,

        onDocumentChange() {
            renderer.update(
                state.document
            );

            canvasEngine.refreshAfterRender();
            inspector.refresh();
        },

        onStatus(message) {
            status.textContent = message;
        },
    });

canvases =
    new CanvasManager({
        root: canvasesRoot,
        state,
        canvas: canvasEngine,
        renderer,

        onDocumentChange() {
            inspector.refresh();
        },

        onStatus(message) {
            status.textContent = message;
        },
    });

components =
    new ComponentLibrary({
        root: componentsRoot,
        state,
        renderer,
        canvas: canvasEngine,
        inspector,

        onStatus(message) {
            status.textContent = message;
        },
    });

experiencePanel =
    new ExperiencePanel({
        root: experienceRoot,
        state,
        assets,

        onPreview() {
            mobilePreview.open({ experience: true });
        },

        onResetPreview() {
            mobilePreview.restartExperience?.();
        },

        onStatus(message) {
            status.textContent = message;
        },
    });

const library =
    new AssetLibrary({
        root: libraryRoot,
        manager: assets,
        uploadService,

        onUse(asset) {
            const node = useAsset({
                state,
                asset,
                selectedNodeId:
                    state.selection.nodeId,
            });

            renderer.update(
                state.document
            );
            canvasEngine.select(node.id);
            inspector.refresh();
        },

        onStatus(message) {
            status.textContent = message;
        },
    });

surface.addEventListener(
    "dragover",
    (event) => {
        event.preventDefault();
        if (event.dataTransfer) {
            event.dataTransfer.dropEffect =
                "copy";
        }
    }
);

surface.addEventListener(
    "drop",
    (event) => {
        event.preventDefault();

        const assetId =
            event.dataTransfer?.getData(
                "application/x-r3-asset"
            );

        const asset =
            assets.use(assetId)
            || assets.get(assetId);

        if (!asset) {
            return;
        }

        const rect =
            surface.getBoundingClientRect();

        const position = {
            x:
                (
                    event.clientX
                    - rect.left
                ) / rect.width * 100,
            y:
                (
                    event.clientY
                    - rect.top
                ) / rect.height * 100,
        };

        const node = useAsset({
            state,
            asset,
            selectedNodeId:
                state.selection.nodeId,
            position,
        });

        renderer.update(
            state.document
        );
        canvasEngine.select(node.id);
        inspector.refresh();
    }
);

document.querySelectorAll(
    "[data-r3-zoom]"
).forEach((button) => {
    button.addEventListener(
        "click",
        () => {
            const value =
                button.dataset.r3Zoom;

            if (value === "fit") {
                const zoom = canvasEngine.fitToViewport({
                    horizontalPadding: 30,
                    verticalPadding: 30,
                });
                updateZoomStatus(zoom);
                return;
            }

            const zoom = canvasEngine.setZoom(
                Number(value)
            );
            updateZoomStatus(zoom);
        }
    );
});



const zoomStatus = document.querySelector("[data-r3-zoom-status]");

function updateZoomStatus(value) {
    if (!zoomStatus) return;
    zoomStatus.textContent = `${Math.round(Number(value || 1) * 100)}%`;
}

document.querySelectorAll("[data-r3-zoom-step]").forEach((button) => {
    button.addEventListener("click", () => {
        const factor = button.dataset.r3ZoomStep === "in" ? 1.1 : 0.9;
        updateZoomStatus(canvasEngine.setZoom(canvasEngine.zoom * factor));
    });
});

viewport.addEventListener("wheel", () => {
    requestAnimationFrame(() => updateZoomStatus(canvasEngine.zoom));
}, { passive: true });

document.querySelector(
    "[data-r3-undo]"
).addEventListener(
    "click",
    () => {
        if (!state.undo()) return;

        renderer.update(
            state.document
        );
        canvasEngine.refreshAfterRender();
        inspector.refresh();
    }
);

document.querySelector(
    "[data-r3-redo]"
).addEventListener(
    "click",
    () => {
        if (!state.redo()) return;

        renderer.update(
            state.document
        );
        canvasEngine.refreshAfterRender();
        inspector.refresh();
    }
);


const leftPanelScrollPositions = new Map();

function getPanelScrollElement(panel) {
    // Cada pestaña izquierda es su propio contexto de scroll.
    // Los widgets internos no deben crear un segundo scroll anidado.
    return panel || null;
}

function rememberLeftPanelScroll(panel) {
    if (!panel) return;
    const scrollElement = getPanelScrollElement(panel);
    leftPanelScrollPositions.set(panel.dataset.r3LeftPanel, {
        top: scrollElement.scrollTop,
        left: scrollElement.scrollLeft,
    });
}

function restoreLeftPanelScroll(panel) {
    if (!panel) return;
    const saved = leftPanelScrollPositions.get(panel.dataset.r3LeftPanel);
    if (!saved) return;
    requestAnimationFrame(() => {
        const scrollElement = getPanelScrollElement(panel);
        scrollElement.scrollTop = saved.top;
        scrollElement.scrollLeft = saved.left;
    });
}

document.querySelectorAll(
    "[data-r3-left-tab]"
).forEach((button) => {
    button.addEventListener(
        "click",
        () => {
            const target =
                button.dataset.r3LeftTab;

            const currentPanel = document.querySelector(
                "[data-r3-left-panel]:not([hidden])"
            );
            rememberLeftPanelScroll(currentPanel);

            document.querySelectorAll(
                "[data-r3-left-tab]"
            ).forEach(
                (item) =>
                    item.classList.toggle(
                        "is-active",
                        item === button
                    )
            );

            let targetPanel = null;

            document.querySelectorAll(
                "[data-r3-left-panel]"
            ).forEach(
                (panel) => {
                    const isTarget =
                        panel.dataset.r3LeftPanel === target;
                    panel.hidden = !isTarget;
                    if (isTarget) targetPanel = panel;
                }
            );

            restoreLeftPanelScroll(targetPanel);
        }
    );
});

document.querySelector(
    "[data-r3-reset-document]"
)?.addEventListener(
    "click",
    () => {
        const confirmed =
            globalThis.confirm
                ? globalThis.confirm(
                    "¿Restablecer el layout de la demo?"
                )
                : true;

        if (!confirmed) {
            return;
        }

        documentStorage.clear();
        globalThis.location.reload();
    }
);

autoLayout.applyAll();
canvasEngine.setZoom(.75);


window.addEventListener(
    "beforeunload",
    () => {
        stopDocumentPersistence.flush?.();
    }
);

globalThis.r3Demo = {
    state,
    assets,
    documentStorage,
    stopDocumentPersistence,
    canvases,
    components,
    experiencePanel,
    mobilePreview,
};
