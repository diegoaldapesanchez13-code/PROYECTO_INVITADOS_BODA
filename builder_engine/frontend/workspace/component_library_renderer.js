import { COMPONENT_LIBRARY_ITEMS, groupLibraryItems } from "./component_library.js";

export function renderComponentLibrary(container, options = {}) {
    if (!container) return;
    const query = String(options.query || "").trim().toLowerCase();
    const filtered = COMPONENT_LIBRARY_ITEMS.filter((item) =>
        !query || [item.label, item.category, item.type].some(
            (value) => String(value).toLowerCase().includes(query)
        )
    );
    const groups = groupLibraryItems(filtered);

    container.innerHTML = `
        <div class="engine-component-library-head">
            <div><strong>Componentes</strong><small>Clic para agregar · arrastra para posicionar</small></div>
            <input type="search" data-component-library-search placeholder="Buscar…" value="${esc(options.query || "")}">
        </div>
        <div class="engine-component-library-groups">
            ${groups.length ? groups.map(renderGroup).join("") : '<p class="engine-library-empty">No se encontraron componentes.</p>'}
        </div>`;
}

function renderGroup(group) {
    return `<section class="engine-component-group">
        <h3>${esc(group.category)}</h3>
        <div class="engine-component-grid">
            ${group.items.map((item) => `
                <button type="button" draggable="true"
                    class="engine-component-item"
                    data-component-library-item="${esc(item.id)}"
                    title="Agregar ${esc(item.label)}">
                    <span>${esc(item.icon)}</span><strong>${esc(item.label)}</strong><small>${esc(item.type)}</small>
                </button>`).join("")}
        </div>
    </section>`;
}

function esc(value) {
    return String(value).replaceAll("&","&amp;").replaceAll("<","&lt;")
        .replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");
}
