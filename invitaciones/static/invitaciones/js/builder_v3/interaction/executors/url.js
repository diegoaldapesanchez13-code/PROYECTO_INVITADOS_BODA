import {
    validateWebUrl,
} from "../validators.js";

export function executeUrl(context) {
    const validation = validateWebUrl(
        context.action.value
    );

    if (!validation.valid) {
        return {
            handled: false,
            status: "invalid",
            type: context.definition.type,
            intent: "OPEN_URL",
            reason: validation.code,
            message: validation.message,
            payload: {
                url: "",
                openInNewTab:
                    Boolean(
                        context.action.openInNewTab
                    ),
            },
        };
    }

    const payload = {
        url: validation.value,
        openInNewTab:
            Boolean(
                context.action.openInNewTab
            ),
    };

    const runtime = context.runtime;

    if (
        !runtime
        || typeof runtime.openUrl
            !== "function"
    ) {
        return {
            handled: true,
            status: "ready",
            type: context.definition.type,
            intent: "OPEN_URL",
            payload,
            runtime: {
                executed: false,
                reason: "runtime-unavailable",
            },
        };
    }

    const runtimeResult =
        runtime.openUrl(
            payload.url,
            {
                openInNewTab:
                    payload.openInNewTab,
                node: context.node,
                event: context.event,
            }
        );

    return {
        handled: true,
        status:
            runtimeResult?.executed
                ? "executed"
                : "ready",
        type: context.definition.type,
        intent: "OPEN_URL",
        payload,
        runtime:
            runtimeResult
            && typeof runtimeResult
                === "object"
                ? { ...runtimeResult }
                : {
                    executed: false,
                    reason:
                        "runtime-result-invalid",
                },
    };
}
