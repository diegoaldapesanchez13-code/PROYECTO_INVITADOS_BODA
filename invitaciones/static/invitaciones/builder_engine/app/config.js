export const BUILDER_MODES = Object.freeze({
    EDIT: "edit",
    PREVIEW: "preview",
    PUBLIC: "public",
});

export function normalizeBuilderConfig(raw = {}) {
    const mode = Object.values(BUILDER_MODES).includes(raw.mode)
        ? raw.mode
        : BUILDER_MODES.EDIT;

    return Object.freeze({
        mode,
        backend: String(raw.backend || "standalone"),
        eventId: raw.eventId ?? null,
        root: raw.root ?? null,
        autosaveDelay: Math.max(Number(raw.autosaveDelay || 3000), 250),
    });
}
