import {
    validateGoogleMapsValue,
} from "../validators.js";

export function executeGoogleMaps(context) {
    const validation =
        validateGoogleMapsValue(
            context.action.value
        );

    if (!validation.valid) {
        return {
            handled: false,
            status: "invalid",
            type: context.definition.type,
            intent: "OPEN_GOOGLE_MAPS",
            reason: validation.code,
            message: validation.message,
            payload: {
                url: "",
                source: null,
                coordinates: null,
                openInNewTab:
                    Boolean(
                        context.action.openInNewTab
                    ),
            },
        };
    }

    const payload = {
        url: validation.value,
        source: validation.source,
        coordinates:
            validation.coordinates,
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
            intent: "OPEN_GOOGLE_MAPS",
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
                interactionType:
                    context.definition.type,
            }
        );

    return {
        handled: true,
        status:
            runtimeResult?.executed
                ? "executed"
                : "ready",
        type: context.definition.type,
        intent: "OPEN_GOOGLE_MAPS",
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
