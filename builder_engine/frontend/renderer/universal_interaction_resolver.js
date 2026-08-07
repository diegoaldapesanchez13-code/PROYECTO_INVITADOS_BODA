import {
    createNodeInteractionContract,
    nodeIsActionable,
} from "../interaction/node_interaction_contract.js";
import { INTERACTION_TYPES } from "../interaction/constants.js";

export function resolveUniversalInteraction(node = {}, context = {}) {
    const contract = createNodeInteractionContract(
        node.interaction || {
            interactions: node.interactions,
            states: node.states,
            ariaLabel: node.ariaLabel || node.content?.alt,
        },
    );

    const actionable = nodeIsActionable({ ...node, interaction: contract });
    const mode = String(context.mode || "EDIT").toUpperCase();

    return {
        contract,
        actionable,
        enabled: actionable && mode !== "EDIT",
        attributes: {
            "aria-label": contract.ariaLabel || node.name || "",
            tabindex: actionable ? "0" : null,
            role: actionable && !nativeInteractive(node.type) ? "button" : null,
            "data-actionable": actionable ? "true" : "false",
        },
    };
}

export function executeUniversalAction(action = {}, runtime = {}) {
    const type = String(action.type || INTERACTION_TYPES.NONE).toUpperCase();
    const value = String(action.value || "");

    switch (type) {
        case INTERACTION_TYPES.URL:
        case INTERACTION_TYPES.GOOGLE_MAPS:
        case INTERACTION_TYPES.WHATSAPP:
            return runtime.openUrl?.(value, {
                newTab: action.openInNewTab,
                target: action.target,
            }) ?? { type: "OPEN_URL", value };
        case INTERACTION_TYPES.NAVIGATE:
            return runtime.navigate?.(value, action.payload)
                ?? { type: "NAVIGATE", value };
        case INTERACTION_TYPES.RSVP:
            return runtime.openRsvp?.(action.payload)
                ?? { type: "RSVP", payload: action.payload };
        case INTERACTION_TYPES.MODAL:
            return runtime.openModal?.(value, action.payload)
                ?? { type: "MODAL", value };
        case INTERACTION_TYPES.DOWNLOAD:
            return runtime.download?.(value, action.payload)
                ?? { type: "DOWNLOAD", value };
        case INTERACTION_TYPES.PLAY_MEDIA:
            return runtime.playMedia?.(value, action.payload)
                ?? { type: "PLAY_MEDIA", value };
        default:
            return { type: "NONE" };
    }
}

function nativeInteractive(type) {
    return ["BUTTON", "LINK"].includes(String(type || "").toUpperCase());
}
