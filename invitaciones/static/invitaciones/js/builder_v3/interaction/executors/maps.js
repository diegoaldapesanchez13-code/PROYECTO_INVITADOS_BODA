export function executeGoogleMaps(context) {
    return {
        handled: true,
        status: "ready",
        type: context.definition.type,
        intent: "OPEN_GOOGLE_MAPS",
        payload: {
            url: context.action.value,
            openInNewTab: context.action.openInNewTab,
        },
    };
}
