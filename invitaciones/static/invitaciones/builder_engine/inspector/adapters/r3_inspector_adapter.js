/**
 * Convierte definiciones de paneles del Inspector R3 al contrato neutral del Engine.
 * No importa DOM ni ejecuta renderizado; solo conserva metadatos y controles.
 */
export function adaptR3Panels(panels = []) {
    return (panels || []).filter(Boolean).map((panel, index) => ({
        id: String(panel.id || panel.title || `r3-panel-${index + 1}`),
        title: String(panel.title || panel.id || `Panel ${index + 1}`),
        kind: panel.kind === "action-group" ? "action-group" : "group",
        order: Number.isFinite(Number(panel.order)) ? Number(panel.order) : index * 10,
        types: normalizeTypes(panel.types || panel.componentTypes || panel.forTypes),
        capabilities: normalizeList(panel.capabilities),
        tab: String(panel.tab || "properties"),
        controls: Array.isArray(panel.controls) ? panel.controls.map(adaptR3Control) : [],
        visible: typeof panel.visible === "function" ? panel.visible : null,
        metadata: { source: "builder-r3", legacyKind: panel.kind || "group" },
    }));
}

export function adaptR3Control(control = {}, index = 0) {
    return {
        id: String(control.id || control.path || control.name || `control-${index + 1}`),
        type: String(control.type || control.kind || "text"),
        label: String(control.label || control.title || ""),
        path: control.path || control.field || null,
        options: Array.isArray(control.options) ? [...control.options] : [],
        min: control.min,
        max: control.max,
        step: control.step,
        metadata: { source: "builder-r3" },
    };
}

function normalizeTypes(value) {
    return normalizeList(value).map((type) => type.toUpperCase());
}
function normalizeList(value) {
    return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}
