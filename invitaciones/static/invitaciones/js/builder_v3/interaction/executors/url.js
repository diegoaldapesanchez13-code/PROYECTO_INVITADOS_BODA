export function executeUrl(context) {
    return intentResult(context, "OPEN_URL", {
        url: context.action.value,
        openInNewTab: context.action.openInNewTab,
    });
}

function intentResult(context, intent, payload) {
    return {
        handled: true,
        status: "ready",
        type: context.definition.type,
        intent,
        payload,
    };
}
