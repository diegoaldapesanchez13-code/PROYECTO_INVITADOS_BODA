export function renderNodeInspector(container, node) {
    if (!container) return;

    const focusState = captureFocusState(container);

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
            <input
                type="text"
                data-node-field="name"
                value="${escapeAttribute(node.name || "")}"
                autocomplete="off"
            >
        </label>

        ${isText ? `
            <label class="engine-field">
                Texto
                <textarea
                    rows="4"
                    data-node-field="content.text"
                    spellcheck="true"
                >${escapeHtml(node.content?.text || "")}</textarea>
            </label>
        ` : ""}

        <div class="engine-property-grid">
            ${numberField("X", "style.x", style.x ?? 50, -200, 200, 0.1)}
            ${numberField("Y", "style.y", style.y ?? 50, -200, 200, 0.1)}
            ${numberField("Ancho %", "style.width", style.width ?? 72, 1, 300, 0.1)}
            ${numberField("Alto %", "style.height", style.height ?? defaultHeight(node), 1, 300, 0.1)}
            ${numberField("Escala", "style.scale", style.scale ?? 1, 0.05, 10, 0.01)}
            ${numberField("Rotación", "style.rotation", style.rotation ?? 0, -360, 360, 1)}
            ${numberField("Opacidad", "style.opacity", style.opacity ?? 1, 0, 1, 0.01)}
            ${numberField("Z-index", "style.zIndex", style.zIndex ?? 1, -100, 999, 1)}
            ${isText ? numberField("Fuente px", "style.fontSize", style.fontSize ?? 24, 6, 300, 1) : ""}
        </div>
    `;

    restoreFocusState(container, focusState);
}

function defaultHeight(node){const s=node?.style||{},w=Number(s.width??72),r=Number(s.aspectRatio||0);if(Number.isFinite(r)&&r>0)return +(w/r).toFixed(2);return {TEXT:12,BUTTON:8,IMAGE:32,VIDEO:44,CARD:28,CONTAINER:34,GROUP:24}[String(node?.type||"").toUpperCase()]||10;}

function numberField(label, path, value, min, max, step) {
    return `
        <label class="engine-field">
            ${label}
            <input
                type="number"
                inputmode="decimal"
                data-node-field="${path}"
                value="${Number(value)}"
                min="${min}"
                max="${max}"
                step="${step}"
                autocomplete="off"
            >
        </label>
    `;
}

function captureFocusState(container) {
    const active = container.ownerDocument?.activeElement;
    if (!active || !container.contains(active)) return null;

    const field = active.dataset?.nodeField;
    if (!field) return null;

    return {
        field,
        selectionStart: safeSelection(active, "selectionStart"),
        selectionEnd: safeSelection(active, "selectionEnd"),
        selectionDirection: active.selectionDirection || "none",
        scrollTop: Number(active.scrollTop || 0),
        scrollLeft: Number(active.scrollLeft || 0),
    };
}

function restoreFocusState(container, state) {
    if (!state?.field) return;

    const selector = `[data-node-field="${cssEscape(state.field)}"]`;
    const field = container.querySelector(selector);
    if (!field) return;

    field.focus({ preventScroll: true });

    if (
        typeof field.setSelectionRange === "function"
        && state.selectionStart !== null
        && state.selectionEnd !== null
    ) {
        try {
            field.setSelectionRange(
                state.selectionStart,
                state.selectionEnd,
                state.selectionDirection,
            );
        } catch {
            // Algunos inputs numéricos no admiten setSelectionRange.
        }
    }

    field.scrollTop = state.scrollTop;
    field.scrollLeft = state.scrollLeft;
}

function safeSelection(element, property) {
    try {
        const value = element[property];
        return Number.isInteger(value) ? value : null;
    } catch {
        return null;
    }
}

function cssEscape(value) {
    return globalThis.CSS?.escape
        ? CSS.escape(String(value))
        : String(value).replaceAll('"', '\\"');
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
