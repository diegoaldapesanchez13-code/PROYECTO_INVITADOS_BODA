export function renderAssetLibrary(container, state = {}) {
    if (!container) return;

    const type = String(state.type || "ALL").toUpperCase();
    const query = String(state.query || "");
    const assets = Array.isArray(state.assets) ? state.assets : [];

    container.innerHTML = `
        <div class="engine-assets-head">
            <div>
                <strong>Biblioteca multimedia</strong>
                <small>${assets.length} archivos disponibles</small>
            </div>
            <input
                type="search"
                data-asset-search
                placeholder="Buscar archivo…"
                value="${escapeHtml(query)}"
            >
        </div>

        <div class="engine-assets-filters">
            ${filterButton("ALL", "Todos", type)}
            ${filterButton("IMAGE", "Imágenes", type)}
            ${filterButton("VIDEO", "Videos", type)}
        </div>

        <div class="engine-assets-grid">
            ${state.loading ? loadingCard() : ""}
            ${state.error ? errorCard(state.error) : ""}
            ${!state.loading && !state.error && !assets.length
                ? emptyCard()
                : assets.map(renderAsset).join("")}
        </div>
    `;
}

function renderAsset(asset) {
    const preview = asset.type === "VIDEO"
        ? `<video src="${escapeHtml(asset.url)}" muted preload="metadata"></video>`
        : `<img src="${escapeHtml(asset.url)}" alt="${escapeHtml(asset.name)}" loading="lazy">`;

    return `
        <button
            type="button"
            class="engine-asset-card"
            data-asset-id="${escapeHtml(asset.id)}"
            data-asset-type="${escapeHtml(asset.type)}"
            title="Usar ${escapeHtml(asset.name)}"
        >
            <span class="engine-asset-preview">${preview}</span>
            <span class="engine-asset-copy">
                <strong>${escapeHtml(asset.name)}</strong>
                <small>${escapeHtml(asset.type)} · ${formatBytes(asset.size)}</small>
            </span>
        </button>
    `;
}

function filterButton(value, label, active) {
    return `
        <button
            type="button"
            class="${value === active ? "active" : ""}"
            data-asset-filter="${value}"
        >${label}</button>
    `;
}

function loadingCard() {
    return '<p class="engine-assets-message">Cargando biblioteca…</p>';
}

function emptyCard() {
    return `
        <div class="engine-assets-empty">
            <span>▧</span>
            <strong>No hay archivos</strong>
            <small>La subida de archivos se habilita en 10.8.2.</small>
        </div>
    `;
}

function errorCard(message) {
    return `<p class="engine-assets-message error">${escapeHtml(message)}</p>`;
}

function formatBytes(value) {
    const bytes = Number(value || 0);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
