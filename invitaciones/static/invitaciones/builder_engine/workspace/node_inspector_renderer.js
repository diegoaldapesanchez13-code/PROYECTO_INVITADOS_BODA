export function renderNodeInspector(container, node) {
    if (!container) return;

    if (!node) {
        container.innerHTML = `
            <div class="engine-inspector-empty">
                <strong>Sin selección</strong>
                <span>Selecciona un elemento en el canvas o en Capas.</span>
            </div>
        `;
        return;
    }

    const isText = String(node.type).toUpperCase() === "TEXT";
    const style = node.style || {};

    container.innerHTML = `
        <div class="engine-node-inspector-head">
            <div>
                <span>${escapeHtml(node.type || "NODE")}</span>
                <strong>${escapeHtml(node.name || node.id || "Elemento")}</strong>
            </div>
            <div class="engine-node-inspector-actions">
                <button type="button" data-engine-node-action="visibility">${node.visible === false ? "Mostrar" : "Ocultar"}</button>
                <button type="button" data-engine-node-action="lock">${node.locked ? "Desbloquear" : "Bloquear"}</button>
                <button class="danger" type="button" data-engine-node-action="delete">Eliminar</button>
            </div>
        </div>

        <label class="engine-field">
            Nombre
            <input type="text" data-node-field="name" value="${escapeAttribute(node.name || "")}">
        </label>

        ${isText ? `
            <label class="engine-field">
                Texto
                <textarea rows="4" data-node-field="content.text">${escapeHtml(node.content?.text || "")}</textarea>
            </label>
        ` : ""}

        <div class="engine-property-grid">
            ${numberField("X", "style.x", style.x ?? 50, -200, 200, 0.1)}
            ${numberField("Y", "style.y", style.y ?? 50, -200, 200, 0.1)}
            ${numberField("Ancho %", "style.width", style.width ?? 72, 1, 300, 0.1)}
            ${numberField("Escala", "style.scale", style.scale ?? 1, 0.05, 10, 0.01)}
            ${numberField("Rotación", "style.rotation", style.rotation ?? 0, -360, 360, 1)}
            ${numberField("Opacidad", "style.opacity", style.opacity ?? 1, 0, 1, 0.01)}
            ${numberField("Z-index", "style.zIndex", style.zIndex ?? 1, -100, 999, 1)}
            ${isText ? numberField("Fuente px", "style.fontSize", style.fontSize ?? 24, 6, 300, 1) : ""}
        </div>
    `;
}

function numberField(label, path, value, min, max, step) {
    return `
        <label class="engine-field">
            ${label}
            <input
                type="number"
                data-node-field="${path}"
                value="${Number(value)}"
                min="${min}"
                max="${max}"
                step="${step}"
            >
        </label>
    `;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
    return escapeHtml(value);
}
