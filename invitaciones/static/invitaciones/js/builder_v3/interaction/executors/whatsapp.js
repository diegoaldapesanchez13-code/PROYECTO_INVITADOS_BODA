export function executeWhatsApp(context) {
    return {
        handled: true,
        status: "ready",
        type: context.definition.type,
        intent: "OPEN_WHATSAPP",
        payload: {
            recipient: context.action.value,
            openInNewTab: context.action.openInNewTab,
        },
    };
}
