export function executeSection(context) {
    return {
        handled: true,
        status: "ready",
        type: context.definition.type,
        intent: "NAVIGATE_SECTION",
        payload: {
            sectionId:
                context.action.target
                || context.action.value,
        },
    };
}
