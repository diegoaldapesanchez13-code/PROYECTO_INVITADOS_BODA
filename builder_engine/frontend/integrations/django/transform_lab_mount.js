import {
    UniversalDomAdapter,
    UniversalRenderer,
    createUniversalRendererFixture,
} from "../../renderer/index.js";
import { SelectionState } from "../../selection/index.js";
import {
    CanvasHeightSession,
    TransformSession,
    createSelectionOverlay,
} from "../../transform/index.js";

const DEVICE_WIDTHS = Object.freeze({
    mobile: 390,
    tablet: 768,
    desktop: 1180,
});

const POINTER_THRESHOLD_PX = 4;

boot().catch((error) => {
    console.error(error);
    setStatus(error.message || "No se pudo iniciar Transform Lab.", "error");
});

async function boot() {
    const root = document.querySelector("[data-transform-lab-root]");
    const bootstrap = document.getElementById(
        root?.dataset.bootstrapId || "dirtec-transform-lab-bootstrap"
    );
    if (!root || !bootstrap) throw new Error("Falta la configuración de Transform Lab.");

    const config = JSON.parse(bootstrap.textContent || "{}");
    const state = {
        renderer: new UniversalRenderer(),
        selection: new SelectionState(),
        document: await loadDocument(config),
        device: "mobile",
        preview: new Map(),
        session: null,
        pointerStart: null,
        pointerMoved: false,
        canvasHeightSession: null,
    };

    bind(root, state);
    render(root, state);

    window.DIRTEC_TRANSFORM_LAB = Object.freeze({
        state,
        render: () => render(root, state),
        cancel: () => cancel(root, state),
    });
}

async function loadDocument(config) {
    try {
        const response = await fetch(config.endpoints.load, {
            credentials: "same-origin",
            headers: { Accept: "application/json" },
        });
        const payload = await response.json();

        if (!response.ok || !payload.ok || !payload.document?.canvases?.length) {
            setStatus("Documento sin lienzos: se usa el fixture.", "warning");
            return createUniversalRendererFixture();
        }

        setStatus(
            `${payload.document.canvases.length} lienzos cargados. Los cambios no se guardan.`,
            "success",
        );
        return payload.document;
    } catch {
        setStatus("No se pudo cargar el documento: se usa el fixture.", "warning");
        return createUniversalRendererFixture();
    }
}

function bind(root, state) {
    root.addEventListener("click", (event) => {
        const deviceButton = event.target.closest("[data-transform-device]");
        if (deviceButton) {
            state.device = deviceButton.dataset.transformDevice;
            state.preview.clear();
            render(root, state);
            return;
        }

        if (event.target.closest("[data-transform-cancel]")) {
            cancel(root, state);
            return;
        }

        if (event.target.closest("[data-transform-reset]")) {
            state.document = createUniversalRendererFixture();
            state.selection.clear();
            state.preview.clear();
            render(root, state);
            setStatus("Fixture restablecido.", "info");
            return;
        }

        const node = event.target.closest(".dirtec-render-node[data-node-id]");
        if (node && !event.target.closest("[data-transform-handle]")) {
            state.selection.select(node.dataset.nodeId);
            renderOverlay(root, state);
        }
    });

    root.addEventListener("pointerdown", (event) => {
        const heightHandle = event.target.closest("[data-canvas-height-handle]");
        if (heightHandle) {
            beginCanvasHeight(event, root, state);
            return;
        }

        const handle = event.target.closest("[data-transform-handle]");
        const nodeElement = event.target.closest(".dirtec-render-node[data-node-id]");
        if (!handle && !nodeElement) return;

        const nodeId = handle?.dataset.nodeId || nodeElement.dataset.nodeId;
        const node = findNode(state.document, nodeId);
        if (!node || node.locked) return;

        const canvas = root.querySelector(".dirtec-render-canvas");
        if (!canvas) return;

        state.selection.select(nodeId);

        const logical = transformPercentToLogical(
            currentTransform(node, state.device),
            state.document.canvases[0],
            state.device,
        );

        state.session = new TransformSession({
            nodeId,
            transform: logical,
            pointer: { x: event.clientX, y: event.clientY },
            operation: handle?.dataset.operation || "MOVE",
            handle: handle?.dataset.position || null,
            zoom: canvasScale(canvas),
        });

        state.pointerStart = { x: event.clientX, y: event.clientY };
        state.pointerMoved = false;

        event.preventDefault();
        event.stopPropagation();
    }, true);

    root.addEventListener("pointermove", (event) => {
        if (state.canvasHeightSession) {
            const height = state.canvasHeightSession.update(event.clientY);
            const canvas = root.querySelector(".dirtec-render-canvas");
            if (canvas) canvas.style.height = `${height}px`;
            positionCanvasHeightHandle(root);
            return;
        }

        if (!state.session || !state.pointerStart) return;

        const distance = Math.hypot(
            event.clientX - state.pointerStart.x,
            event.clientY - state.pointerStart.y,
        );

        if (!state.pointerMoved && distance < POINTER_THRESHOLD_PX) {
            return;
        }

        state.pointerMoved = true;
        root.dataset.transforming = "true";

        const value = state.session.update({
            x: event.clientX,
            y: event.clientY,
        });

        state.preview.set(state.session.nodeId, value);
        applyPreview(root, state.session.nodeId, value);
        renderOverlay(root, state);
    }, true);

    root.addEventListener("pointerup", () => {
        if (state.canvasHeightSession) {
            const transaction = state.canvasHeightSession.commit();
            writeCanvasHeight(state.document.canvases[0], state.device, transaction.after);
            state.canvasHeightSession = null;
            render(root, state);
            setStatus(`Altura: ${Math.round(transaction.after)} px. Solo memoria.`, "success");
            return;
        }

        if (!state.session) return;

        if (!state.pointerMoved) {
            state.session.cancel();
            state.session = null;
            state.pointerStart = null;
            state.pointerMoved = false;
            root.dataset.transforming = "false";
            renderOverlay(root, state);
            return;
        }

        const transaction = state.session.commit();
        writeNodeTransform(
            state.document,
            transaction.nodeId,
            transaction.after,
            state.device,
        );

        state.preview.delete(transaction.nodeId);
        state.session = null;
        state.pointerStart = null;
        state.pointerMoved = false;
        root.dataset.transforming = "false";
        render(root, state);
        setStatus(`${transaction.operation} confirmado. Solo memoria.`, "success");
    }, true);

    root.addEventListener("pointercancel", () => cancel(root, state), true);
    window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") cancel(root, state);
    });
    window.addEventListener("resize", () => {
        scaleStage(root);
        renderOverlay(root, state);
        positionCanvasHeightHandle(root);
    });
}

function render(root, state) {
    updateDeviceButtons(root, state.device);

    const canvas = state.document.canvases?.[0];
    const target = root.querySelector("[data-transform-render-target]");
    if (!canvas || !target) return;

    const document = {
        ...state.document,
        canvases: [{
            ...canvas,
            nodes: applyPreviewTree(canvas.nodes || [], state.preview, state.device, canvas),
        }],
    };

    const result = state.renderer.renderDocument(document, {
        mode: "EDIT",
        device: state.device,
    });

    new UniversalDomAdapter().mount(result, target);

    requestAnimationFrame(() => {
        scaleStage(root);
        renderOverlay(root, state);
        positionCanvasHeightHandle(root);
    });
}

function renderOverlay(root, state) {
    const overlayRoot = root.querySelector("[data-transform-overlay-root]");
    overlayRoot?.replaceChildren();

    const nodeId = state.selection.primaryId;
    if (!overlayRoot || !nodeId) return;

    const node = findNode(state.document, nodeId);
    const element = root.querySelector(
        `.dirtec-render-node[data-node-id="${escapeCss(nodeId)}"]`
    );
    const canvas = element?.closest(".dirtec-render-canvas");
    if (!node || !element || !canvas) return;

    const rect = element.getBoundingClientRect();
    const hostRect = overlayRoot.getBoundingClientRect();

    const previewRotation = state.preview.get(nodeId)?.rotation;
    const rotation = Number(
        previewRotation ?? currentTransform(node, state.device).rotation ?? 0
    );

    const overlay = createSelectionOverlay(node, {
        frame: {
            x: rect.left - hostRect.left,
            y: rect.top - hostRect.top,
            width: rect.width,
            height: rect.height,
            rotation,
        },
    });

    const frame = document.createElement("div");
    frame.className = "transform-lab-frame";
    frame.style.left = `${rect.left - hostRect.left}px`;
    frame.style.top = `${rect.top - hostRect.top}px`;
    frame.style.width = `${rect.width}px`;
    frame.style.height = `${rect.height}px`;
    frame.style.transform = `rotate(${overlay.frame.rotation}deg)`;

    for (const item of overlay.handles) {
        const handle = document.createElement("button");
        handle.type = "button";
        handle.className = `transform-lab-handle ${item.position}`;
        handle.dataset.transformHandle = item.id;
        handle.dataset.operation = item.operation;
        handle.dataset.position = item.position;
        handle.dataset.nodeId = nodeId;
        frame.append(handle);
    }

    if (overlay.rotationHandle) {
        const rotate = document.createElement("button");
        rotate.type = "button";
        rotate.className = "transform-lab-handle rotate";
        rotate.dataset.transformHandle = "rotate";
        rotate.dataset.operation = "ROTATE";
        rotate.dataset.nodeId = nodeId;
        rotate.textContent = "↻";
        frame.append(rotate);
    }

    overlayRoot.append(frame);
}

function beginCanvasHeight(event, root, state) {
    const canvasNode = state.document.canvases[0];
    state.canvasHeightSession = new CanvasHeightSession({
        height: canvasHeight(canvasNode, state.device),
        pointerY: event.clientY,
        zoom: canvasScale(root.querySelector(".dirtec-render-canvas")),
        minHeight: 320,
        maxHeight: 12000,
    });
    event.preventDefault();
    event.stopPropagation();
}

function cancel(root, state) {
    if (state.session) {
        state.session.cancel();
        state.preview.delete(state.session.nodeId);
        state.session = null;
    }
    if (state.canvasHeightSession) {
        state.canvasHeightSession.cancel();
        state.canvasHeightSession = null;
    }

    state.pointerStart = null;
    state.pointerMoved = false;
    root.dataset.transforming = "false";
    render(root, state);
    setStatus("Operación cancelada.", "info");
}

function applyPreview(root, nodeId, value) {
    const element = root.querySelector(
        `.dirtec-render-node[data-node-id="${escapeCss(nodeId)}"]`
    );
    const canvas = element?.closest(".dirtec-render-canvas");
    if (!element || !canvas) return;

    const width = Number.parseFloat(canvas.style.width) || DEVICE_WIDTHS.mobile;
    const height = Number.parseFloat(canvas.style.height) || 844;

    element.style.left = `${value.x / width * 100}%`;
    element.style.top = `${value.y / height * 100}%`;
    element.style.width = `${value.width / width * 100}%`;
    element.style.height = `${value.height / height * 100}%`;
    element.style.translate = "0 0";
    element.style.transformOrigin = "0 0";
    element.style.transform = `rotate(${value.rotation}deg)`;
}

function applyPreviewTree(nodes, preview, device, canvas) {
    return nodes.map((node) => {
        const next = {
            ...node,
            children: applyPreviewTree(node.children || [], preview, device, canvas),
        };
        const value = preview.get(node.id);
        if (!value) return next;

        next.layout = structuredClone(node.layout || {
            transform: {},
            responsive: {},
        });

        const patch = logicalToPercent(value, canvas, device);
        patch.originX = 0;
        patch.originY = 0;

        if (device === "mobile") {
            next.layout.transform = {
                ...(next.layout.transform || {}),
                ...patch,
            };
        } else {
            next.layout.responsive = next.layout.responsive || {};
            next.layout.responsive[device] = {
                ...(next.layout.responsive[device] || {}),
                ...patch,
            };
        }
        return next;
    });
}

function writeNodeTransform(documentValue, nodeId, value, device) {
    const node = findNode(documentValue, nodeId);
    const canvas = documentValue.canvases[0];
    if (!node || !canvas) return;

    const patch = {
        ...logicalToPercent(value, canvas, device),
        originX: 0,
        originY: 0,
    };

    node.layout = node.layout || { transform: {}, responsive: {} };

    if (device === "mobile") {
        node.layout.transform = { ...(node.layout.transform || {}), ...patch };
    } else {
        node.layout.responsive = node.layout.responsive || {};
        node.layout.responsive[device] = {
            ...(node.layout.responsive[device] || {}),
            ...patch,
        };
    }
}

function transformPercentToLogical(transform, canvas, device) {
    const width = DEVICE_WIDTHS[device] || 390;
    const height = canvasHeight(canvas, device);
    const originX = Number(transform.originX ?? 0.5);
    const originY = Number(transform.originY ?? 0.5);
    const nodeWidth = Number(transform.width || 0) / 100 * width;
    const nodeHeight = Number(transform.height || 0) / 100 * height;

    return {
        x: Number(transform.x || 0) / 100 * width - nodeWidth * originX,
        y: Number(transform.y || 0) / 100 * height - nodeHeight * originY,
        width: nodeWidth,
        height: nodeHeight,
        rotation: Number(transform.rotation || 0),
        opacity: Number(transform.opacity ?? 1),
        originX: 0,
        originY: 0,
    };
}

function logicalToPercent(value, canvas, device) {
    const width = DEVICE_WIDTHS[device] || 390;
    const height = canvasHeight(canvas, device);

    return {
        x: value.x / width * 100,
        y: value.y / height * 100,
        width: value.width / width * 100,
        height: value.height / height * 100,
        rotation: value.rotation,
    };
}

function currentTransform(node, device) {
    const base = node.layout?.transform || {};
    return {
        ...base,
        ...(node.layout?.responsive?.[device] || {}),
    };
}

function writeCanvasHeight(canvas, device, height) {
    canvas.size = canvas.size || {};
    canvas.size.responsive = canvas.size.responsive || {};
    canvas.size.responsive[device] = {
        ...(canvas.size.responsive[device] || {}),
        height,
    };
}

function canvasHeight(canvas, device) {
    return Number(
        canvas.size?.responsive?.[device]?.height
        ?? canvas.size?.responsive?.mobile?.height
        ?? canvas.height
        ?? 844
    );
}

function scaleStage(root) {
    const stage = root.querySelector("[data-transform-stage]");
    const host = root.querySelector(".transform-lab-render-host");
    const canvas = root.querySelector(".dirtec-render-canvas");
    if (!stage || !host || !canvas) return;

    const logicalWidth = Number.parseFloat(canvas.style.width) || 390;
    const available = Math.max(stage.clientWidth - 80, 1);
    const scale = Math.min(1, available / logicalWidth);

    host.style.transform = `scale(${scale})`;
    host.style.transformOrigin = "top center";
    stage.style.setProperty(
        "--transform-stage-height",
        `${Math.max(canvas.offsetHeight * scale + 120, 560)}px`
    );
}

function positionCanvasHeightHandle(root) {
    const canvas = root.querySelector(".dirtec-render-canvas");
    const handle = root.querySelector("[data-canvas-height-handle]");
    const stage = root.querySelector("[data-transform-stage]");
    if (!canvas || !handle || !stage) return;

    const canvasRect = canvas.getBoundingClientRect();
    const stageRect = stage.getBoundingClientRect();

    handle.style.left = `${canvasRect.left - stageRect.left + stage.scrollLeft}px`;
    handle.style.top = `${canvasRect.bottom - stageRect.top + stage.scrollTop - 2}px`;
    handle.style.width = `${canvasRect.width}px`;
}

function canvasScale(canvas) {
    if (!canvas) return 1;
    const logical = Number.parseFloat(canvas.style.width) || canvas.offsetWidth || 390;
    return canvas.getBoundingClientRect().width / logical || 1;
}

function findNode(documentValue, nodeId) {
    for (const canvas of documentValue.canvases || []) {
        const found = findNodeIn(canvas.nodes || [], nodeId);
        if (found) return found;
    }
    return null;
}

function findNodeIn(nodes, nodeId) {
    for (const node of nodes) {
        if (node.id === nodeId) return node;
        const found = findNodeIn(node.children || [], nodeId);
        if (found) return found;
    }
    return null;
}

function updateDeviceButtons(root, device) {
    for (const button of root.querySelectorAll("[data-transform-device]")) {
        button.classList.toggle(
            "active",
            button.dataset.transformDevice === device,
        );
    }
}

function setStatus(message, type = "info") {
    const status = document.querySelector("[data-transform-lab-status]");
    if (!status) return;
    status.textContent = message;
    status.dataset.type = type;
}

function escapeCss(value) {
    return globalThis.CSS?.escape
        ? CSS.escape(value)
        : String(value).replaceAll('"', '\\"');
}
