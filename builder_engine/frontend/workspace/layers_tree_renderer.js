export function renderLayersTree(container, nodes, options = {}) {
    if (!container) return;

    const selectedId = options.selectedId || null;
    container.innerHTML = "";

    if (!nodes?.length) {
        container.innerHTML = '<p class="engine-layers-empty">Sin elementos</p>';
        return;
    }

    const list = document.createElement("div");
    list.className = "engine-layers-tree";
    for (const node of nodes) {
        list.appendChild(renderLayerNode(node, selectedId, 0));
    }
    container.appendChild(list);
}

function renderLayerNode(node, selectedId, depth) {
    const wrapper = document.createElement("div");
    wrapper.className = "engine-layer-node";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "engine-layer-select";
    if (node.id === selectedId) button.classList.add("active");
    button.dataset.engineNodeAction = "select";
    button.dataset.nodeId = node.id || "";
    button.style.setProperty("--layer-depth", String(depth));

    button.innerHTML = `
        <span class="engine-layer-icon">${iconFor(node.type)}</span>
        <span class="engine-layer-copy">
            <strong>${escapeHtml(node.name || node.type || "Elemento")}</strong>
            <small>${escapeHtml(node.type || "NODE")}</small>
        </span>
        <span class="engine-layer-state">${node.locked ? "🔒" : ""}${node.visible === false ? "○" : "●"}</span>
    `;
    wrapper.appendChild(button);

    if (node.children?.length) {
        const children = document.createElement("div");
        children.className = "engine-layer-children";
        for (const child of node.children) {
            children.appendChild(renderLayerNode(child, selectedId, depth + 1));
        }
        wrapper.appendChild(children);
    }

    return wrapper;
}

function iconFor(type) {
    return {
        TEXT: "T",
        IMAGE: "▧",
        VIDEO: "▶",
        BUTTON: "B",
        CARD: "C",
        CONTAINER: "□",
        COUNTDOWN: "◷",
    }[String(type || "").toUpperCase()] || "•";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
