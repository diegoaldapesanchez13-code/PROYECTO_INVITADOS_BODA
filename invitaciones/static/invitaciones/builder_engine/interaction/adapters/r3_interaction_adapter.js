import { createInteraction } from "../interaction_contract.js";

const TYPE_MAP = Object.freeze({
    NONE: "NONE",
    URL: "URL",
    GOOGLE_MAPS: "GOOGLE_MAPS",
    WHATSAPP: "WHATSAPP",
    SECTION: "CANVAS",
});

export function adaptR3Interaction(value = {}) {
    const action = value.action || {};
    return createInteraction({
        enabled: value.enabled,
        trigger: value.trigger || "CLICK",
        action: {
            type: TYPE_MAP[String(action.type || "NONE").toUpperCase()] || "NONE",
            value: action.value,
            target: action.target,
            openInNewTab: action.openInNewTab,
            payload: action.payload || {},
        },
    });
}
