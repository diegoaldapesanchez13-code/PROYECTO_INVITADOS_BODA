export const RENDERER_MODULE_KEY = "renderer";

export const RENDER_MODES = Object.freeze({
    EDIT: "EDIT",
    PREVIEW: "PREVIEW",
    PUBLIC: "PUBLIC",
});

export const DEFAULT_RENDER_MODE = RENDER_MODES.EDIT;

export function normalizeRenderMode(value) {
    const mode = String(value || DEFAULT_RENDER_MODE).trim().toUpperCase();
    if (!Object.values(RENDER_MODES).includes(mode)) {
        throw new RangeError(`Modo de render no soportado: ${value}`);
    }
    return mode;
}
