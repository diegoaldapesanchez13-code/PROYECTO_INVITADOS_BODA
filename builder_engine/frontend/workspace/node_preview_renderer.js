export function renderCanvasPreview(canvas, options = {}) {
    const assets = new Map(
        (options.assets || []).map((asset) => [String(asset.id), asset]),
    );

    const root = document.createElement("div");
    root.className = "engine-live-canvas";
    root.dataset.canvasId = canvas.id;
    root.style.minHeight = `${Number(canvas.height || 700)}px`;

    if (canvas.background?.color) root.style.backgroundColor = canvas.background.color;

    for (const node of orderedNodes(canvas.nodes || [])) {
        const element = renderNode(node, assets, options.selectedNodeId);
        if (element) root.appendChild(element);
    }

    if (!root.children.length) {
        const empty = document.createElement("div");
        empty.className = "engine-live-empty";
        empty.innerHTML = "<strong>Lienzo vacío</strong><span>Agrega componentes en el siguiente sprint.</span>";
        root.appendChild(empty);
    }

    return root;
}

function renderNode(node, assets, selectedNodeId) {
    if (!node || node.visible === false) return null;

    let element;
    switch (String(node.type || "").toUpperCase()) {
        case "TEXT":
            element = document.createElement(node.content?.tag || "div");
            element.textContent = node.content?.text || "";
            break;
        case "IMAGE":
            element = document.createElement("img");
            element.alt = node.content?.alt || node.name || "";
            element.src = resolveUrl(node, assets);
            break;
        case "VIDEO":
            element = document.createElement("video");
            element.src = resolveUrl(node, assets);
            element.controls = Boolean(node.content?.controls ?? true);
            element.muted = Boolean(node.content?.muted ?? true);
            break;
        case "BUTTON":
            element = document.createElement("button");
            element.type = "button";
            element.textContent = node.content?.label || node.content?.text || "Botón";
            break;
        case "COUNTDOWN":
        case "CARD":
        case "CONTAINER":
        case "GROUP":
            element = document.createElement("div");
            for (const child of node.children || []) {
                const childElement = renderNode(child, assets, selectedNodeId);
                if (childElement) element.appendChild(childElement);
            }
            break;
        default:
            element = document.createElement("div");
            element.textContent = node.name || node.type || "Elemento";
    }

    element.classList.add("engine-preview-node");
    if (node.id === selectedNodeId) element.classList.add("is-selected");
    element.dataset.engineNodeAction = "select";
    element.dataset.nodeId = node.id || "";
    element.dataset.nodeType = node.type || "";
    applyStyle(element, node.style || {}, node.type);
    return element;
}

function applyStyle(element, style, type) {
    element.style.position = "absolute";
    element.style.left = `${number(style.x, 50)}%`;
    element.style.top = `${number(style.y, 50)}%`;
    element.style.width = `${number(style.width, type === "IMAGE" ? 42 : 72)}%`;
    element.style.opacity = String(number(style.opacity, 1));
    element.style.zIndex = String(number(style.zIndex, 1));
    element.style.transform = [
        "translate(-50%, -50%)",
        `scale(${number(style.scale, 1)})`,
        `rotate(${number(style.rotation, 0)}deg)`,
    ].join(" ");
    element.style.textAlign = style.textAlign || "center";
    element.style.cursor = "pointer";

    if (element.tagName === "IMG" || element.tagName === "VIDEO") {
        element.style.height = "auto";
        element.style.objectFit = style.fit || "contain";
    }
    if (style.fontSize) element.style.fontSize = `${number(style.fontSize, 24)}px`;
    if (style.fontWeight) element.style.fontWeight = String(style.fontWeight);
    if (style.color) element.style.color = style.color;
    if (style.backgroundColor) element.style.backgroundColor = style.backgroundColor;
    if (style.borderRadius != null) {
        element.style.borderRadius = `${number(style.borderRadius, 0)}px`;
    }
}

function resolveUrl(node, assets) {
    if (node.content?.url) return node.content.url;
    const asset = assets.get(String(node.content?.assetId || ""));
    return asset?.url || "";
}

function orderedNodes(nodes) {
    return [...nodes].sort(
        (a, b) => number(a.style?.zIndex, 0) - number(b.style?.zIndex, 0),
    );
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
