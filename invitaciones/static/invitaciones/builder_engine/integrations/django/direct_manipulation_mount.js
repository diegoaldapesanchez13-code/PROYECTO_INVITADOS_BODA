import {
    DirectManipulationController,
    createTransformOverlay,
    positionTransformOverlay,
    DEVICE_PROFILES,
} from "../../workspace/index.js";

waitForBuilder().then(mount).catch((error) => {
    console.error("No se pudo montar la manipulación directa.", error);
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
    const activeCanvas = root?.querySelector("[data-engine-active-canvas]");
    if (!root || !activeCanvas) return;

    const controller = new DirectManipulationController({
        nodeWorkspace: builder.nodeWorkspace,
        workspace: builder.workspace,
    });

    const overlay = createTransformOverlay();

    let pointerId = null;
    let previewTransform = null;
    let activeElement = null;
    let activeLiveCanvas = null;

    const findSelectedElement = () => {
        const nodeId = builder.nodeWorkspace.selectedNodeId || "";
        if (!nodeId) return null;

        return activeCanvas.querySelector(
            `.engine-preview-node[data-node-id="${escapeCss(nodeId)}"]`
        );
    };

    const attachOverlayToCanvas = (liveCanvas) => {
        if (!liveCanvas) {
            overlay.hidden = true;
            return;
        }

        if (overlay.parentElement !== liveCanvas) {
            liveCanvas.appendChild(overlay);
        }
    };

    const refreshOverlay = () => {
        activeElement = findSelectedElement();
        activeLiveCanvas = activeElement?.closest(".engine-live-canvas") || null;

        if (!activeElement || !activeLiveCanvas) {
            overlay.hidden = true;
            return;
        }

        attachOverlayToCanvas(activeLiveCanvas);
        positionTransformOverlay(overlay, activeElement, activeLiveCanvas);
        syncDeviceButtons(root, controller.device);
    };

    root.addEventListener("click", (event) => {
        const button = event.target.closest("[data-engine-device]");
        if (!button) return;

        controller.setDevice(button.dataset.engineDevice);
        applyDeviceWidth(activeCanvas, controller.device);

        builder.app.replaceDocument(builder.app.getDocument(), {
            markDirty: false,
            source: "workspace-device",
        });

        requestAnimationFrame(refreshOverlay);
    });

    root.addEventListener("pointerdown", (event) => {
        const handle = event.target.closest("[data-transform-mode]");
        const selected = event.target.closest(".engine-preview-node.is-selected");

        if (!handle && !selected) return;
        if (event.button !== 0) return;

        const targetNode = handle ? activeElement : selected;
        const liveCanvas = targetNode?.closest(".engine-live-canvas");

        if (!targetNode || !liveCanvas) return;

        event.preventDefault();
        event.stopPropagation();

        activeElement = targetNode;
        activeLiveCanvas = liveCanvas;
        attachOverlayToCanvas(liveCanvas);

        const mode = handle?.dataset.transformMode || "drag";
        const rect = targetNode.getBoundingClientRect();
        const canvasRect = liveCanvas.getBoundingClientRect();

        controller.begin(mode, event, {
            canvasWidth: canvasRect.width,
            canvasHeight: canvasRect.height,
            center: {
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
            },
            handle: handle?.dataset.handle || "se",
        });

        pointerId = event.pointerId;
        previewTransform = null;

        event.target.setPointerCapture?.(pointerId);
        root.dataset.transforming = "true";
    }, true);

    root.addEventListener("pointermove", (event) => {
        if (
            !controller.active
            || event.pointerId !== pointerId
            || !activeElement
            || !activeLiveCanvas
        ) return;

        previewTransform = controller.preview(event, {
            shiftKey: event.shiftKey,
            altKey: event.altKey,
        });

        applyPreview(activeElement, previewTransform);

        requestAnimationFrame(() => {
            positionTransformOverlay(
                overlay,
                activeElement,
                activeLiveCanvas,
            );
        });
    }, true);

    const finish = (event, commit) => {
        if (!controller.active || event.pointerId !== pointerId) return;

        if (commit && previewTransform) {
            controller.commit(previewTransform);
        } else {
            controller.cancel();
        }

        pointerId = null;
        previewTransform = null;
        activeElement = null;
        activeLiveCanvas = null;
        root.dataset.transforming = "false";

        requestAnimationFrame(refreshOverlay);
    };

    root.addEventListener("pointerup", (event) => finish(event, true), true);
    root.addEventListener("pointercancel", (event) => finish(event, false), true);

    activeCanvas.addEventListener("scroll", () => {
        requestAnimationFrame(refreshOverlay);
    }, true);

    window.addEventListener("resize", () => {
        requestAnimationFrame(refreshOverlay);
    });

    const observer = new MutationObserver(() => {
        requestAnimationFrame(refreshOverlay);
    });

    observer.observe(activeCanvas, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ["style", "class", "data-node-id"],
    });

    applyDeviceWidth(activeCanvas, controller.device);
    refreshOverlay();

    window.DIRTEC_BUILDER_TRANSFORM = Object.freeze({
        controller,
        refreshOverlay,
    });
}

function applyPreview(element, style) {
    element.style.left = `${number(style.x, 50)}%`;
    element.style.top = `${number(style.y, 50)}%`;
    element.style.width = `${number(style.width, 72)}%`;
    element.style.transform = [
        "translate(-50%, -50%)",
        `scale(${number(style.scale, 1)})`,
        `rotate(${number(style.rotation, 0)}deg)`,
    ].join(" ");
}

function applyDeviceWidth(container, device) {
    const profile = DEVICE_PROFILES[device] || DEVICE_PROFILES.mobile;
    container.dataset.previewDevice = profile.key;
    container.style.setProperty("--preview-width", `${profile.width}px`);
}

function syncDeviceButtons(root, device) {
    for (const button of root.querySelectorAll("[data-engine-device]")) {
        button.classList.toggle(
            "active",
            button.dataset.engineDevice === device,
        );
    }
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function escapeCss(value) {
    return globalThis.CSS?.escape
        ? CSS.escape(value)
        : String(value).replaceAll('"', '\\"');
}
