export const INTERACTION_TRIGGERS = Object.freeze({
    CLICK: "CLICK",
});

export const INTERACTION_TYPES = Object.freeze({
    NONE: "NONE",
    URL: "URL",
    GOOGLE_MAPS: "GOOGLE_MAPS",
    WHATSAPP: "WHATSAPP",
    SECTION: "SECTION",
});

export function createDefaultInteraction(overrides = {}) {
    const rawAction = plainObject(overrides.action);

    return {
        enabled: Boolean(overrides.enabled ?? false),
        trigger: enumValue(
            overrides.trigger,
            Object.values(INTERACTION_TRIGGERS),
            INTERACTION_TRIGGERS.CLICK
        ),
        action: {
            type: enumValue(
                rawAction.type,
                Object.values(INTERACTION_TYPES),
                INTERACTION_TYPES.NONE
            ),
            value: stringValue(rawAction.value),
            target: stringValue(rawAction.target),
            openInNewTab: Boolean(
                rawAction.openInNewTab ?? false
            ),
        },
    };
}

export function normalizeInteraction(value = {}) {
    return createDefaultInteraction(
        plainObject(value)
    );
}

function enumValue(value, values, fallback) {
    return values.includes(value)
        ? value
        : fallback;
}

function stringValue(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value);
}

function plainObject(value) {
    return (
        value
        && typeof value === "object"
        && !Array.isArray(value)
    )
        ? value
        : {};
}
