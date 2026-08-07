export function executeNone(context) {
    return {
        handled: false,
        status: "skipped",
        reason: "interaction-type-none",
        type: context.definition.type,
        intent: null,
        payload: null,
    };
}
