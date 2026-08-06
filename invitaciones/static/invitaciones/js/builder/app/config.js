export const BUILDER_MODES = Object.freeze({
    EDIT: "edit",
    PREVIEW: "preview",
    PUBLIC: "public",
});

export function normalizeBuilderConfig(config = {}) {
    return {
        backend: String(config.backend || "standalone"),
        mode: Object.values(BUILDER_MODES).includes(config.mode)
            ? config.mode
            : BUILDER_MODES.EDIT,
        eventId: config.eventId ?? null,
        autosaveDelay: Math.max(Number(config.autosaveDelay || 3000), 250),
    };
}
