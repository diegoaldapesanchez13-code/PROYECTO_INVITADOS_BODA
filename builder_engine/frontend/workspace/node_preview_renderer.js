import { resolveResponsiveStyle } from "./transform_math.js";

export function renderCanvasPreview(canvas, options = {}) {
    const assets = new Map(
        (options.assets || []).map((asset) => [String(asset.id), asset]),
    );
    const device = options.device || "mobile";

    const root = document.createElement("div");
    root.className = "engine-live-canvas";
    root.dataset.canvasId = canvas.id;
    root.dataset.previewDevice = device;
    root.style.minHeight = `${Number(canvas.height || 700)}px`;
    if (canvas.background?.color) root.style.backgroundColor = canvas.background.color;

    for (const node of orderedNodes(canvas.nodes || [], device)) {
        const element = renderNode(node, assets, options.selectedNodeId, device, false);
        if (element) root.appendChild(element);
    }

    if (!root.children.length) {
        const empty = document.createElement("div");
        empty.className = "engine-live-empty";
        empty.innerHTML = "<strong>Lienzo vacío</strong><span>Agrega componentes desde el menú.</span>";
        root.appendChild(empty);
    }
    return root;
}

function renderNode(node, assets, selectedNodeId, device, nested) {
    if (!node || node.visible === false) return null;

    const type = String(node.type || "").toUpperCase();
    const mediaUrl = resolveUrl(node, assets);
    let element;

    if (type === "TEXT") {
        element = document.createElement(node.content?.tag || "div");
        element.textContent = node.content?.text || "";
    } else if (type === "IMAGE" && mediaUrl) {
        element = document.createElement("img");
        element.alt = node.content?.alt || node.name || "";
        element.src = mediaUrl;
    } else if (type === "IMAGE") {
        element = placeholder("▧", "Selecciona una imagen", "IMAGE");
    } else if (type === "VIDEO" && mediaUrl) {
        element = document.createElement("video");
        element.src = mediaUrl;
        element.controls = Boolean(node.content?.controls ?? true);
        element.muted = Boolean(node.content?.muted ?? true);
    } else if (type === "VIDEO") {
        element = placeholder("▶", "Selecciona un video o YouTube", "VIDEO");
    } else if (type === "BUTTON") {
        element = document.createElement("button");
        element.type = "button";
        element.textContent = node.content?.label || node.content?.text || "Botón";
    } else if (type === "SEPARATOR") {
        element = document.createElement("hr");
    } else if (["COUNTDOWN", "CARD", "CONTAINER", "GROUP"].includes(type)) {
        element = document.createElement("div");
        element.classList.add(`engine-preview-${type.toLowerCase()}`);
        for (const child of node.children || []) {
            const childElement = renderNode(child, assets, selectedNodeId, device, true);
            if (childElement) element.appendChild(childElement);
        }
    } else {
        element = document.createElement("div");
        element.textContent = node.name || node.type || "Elemento";
    }

    element.classList.add("engine-preview-node");
    if (node.id === selectedNodeId) element.classList.add("is-selected");
    element.dataset.engineNodeAction = "select";
    element.dataset.nodeId = node.id || "";
    element.dataset.nodeType = node.type || "";

    applyStyle(
        element,
        resolveResponsiveStyle(node.style || {}, device),
        type,
        nested,
    );
    return element;
}

function placeholder(icon, message, type) {
    const element = document.createElement("div");
    element.className = "engine-media-placeholder";
    element.innerHTML = `<span>${icon}</span><strong>${message}</strong><small>${type}</small>`;
    return element;
}

function applyStyle(element, style, type, nested) {
    if (nested) {
        element.style.position = "relative";
        element.style.left = "auto";
        element.style.top = "auto";
        element.style.width = style.width ? `${number(style.width, 100)}%` : "auto";
        if (style.height != null) element.style.height = `${number(style.height, 12)}%`;
        element.style.transform = "none";
    } else {
        element.style.position = "absolute";
        element.style.left = `${number(style.x, 50)}%`;
        element.style.top = `${number(style.y, 50)}%`;
        element.style.width = `${number(style.width, type === "IMAGE" ? 42 : 72)}%`;
        element.style.height = `${number(style.height, defaultHeight(type, style))}%`;
        element.style.transform = [
            "translate(-50%, -50%)",
            `scale(${number(style.scale, 1)})`,
            `rotate(${number(style.rotation, 0)}deg)`,
        ].join(" ");
    }

    element.style.opacity = String(number(style.opacity, 1));
    element.style.zIndex = String(number(style.zIndex, 1));
    element.style.textAlign = style.textAlign || "center";
    element.style.cursor = "move";
    element.style.touchAction = "none";

    if (style.minHeight) element.style.minHeight = `${number(style.minHeight, 0)}px`;
    if (style.padding) element.style.padding = `${number(style.padding, 0)}px`;
    if (style.gap) element.style.gap = `${number(style.gap, 0)}px`;
    if (style.backgroundColor) element.style.backgroundColor = style.backgroundColor;
    if (style.color) element.style.color = style.color;
    if (style.borderRadius != null) {
        element.style.borderRadius = `${number(style.borderRadius, 0)}px`;
    }
    if (style.fontSize) element.style.fontSize = `${number(style.fontSize, 24)}px`;
    if (style.fontWeight) element.style.fontWeight = String(style.fontWeight);
    if (style.lineHeight) element.style.lineHeight = String(style.lineHeight);

    if (["COUNTDOWN", "CONTAINER", "CARD", "GROUP"].includes(type)) {
        element.style.display = "flex";
        element.style.flexDirection = style.direction || (type === "COUNTDOWN" ? "row" : "column");
        element.style.justifyContent = "center";
        element.style.alignItems = "stretch";
    }

    if (element.tagName === "IMG" || element.tagName === "VIDEO") {
        element.style.objectFit = style.fit || "cover";
        element.style.display = "block";
    }

    if (type === "BUTTON") { element.style.display="flex"; element.style.alignItems="center"; element.style.justifyContent="center"; }
    if (type === "TEXT") { element.style.overflow=style.overflow||"visible"; element.style.margin="0"; }

    if (element.tagName === "HR") {
        element.style.border = "0";
        element.style.borderTop = `${number(style.borderWidth, 1)}px solid ${style.color || "#8c8c8c"}`;
    }
}

function defaultHeight(type,style={}){const w=number(style.width,type==="IMAGE"?42:72),r=number(style.aspectRatio,0);if(r>0)return w/r;return {TEXT:12,BUTTON:8,IMAGE:32,VIDEO:44,CARD:28,CONTAINER:34,GROUP:24}[type]||10;}

function resolveUrl(node, assets) {
    if (node.content?.url) return node.content.url;
    if (node.content?.source) return node.content.source;
    return assets.get(String(node.content?.assetId || ""))?.url || "";
}

function orderedNodes(nodes, device) {
    return [...nodes].sort(
        (a, b) => number(resolveResponsiveStyle(a.style || {}, device).zIndex, 0)
            - number(resolveResponsiveStyle(b.style || {}, device).zIndex, 0),
    );
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
