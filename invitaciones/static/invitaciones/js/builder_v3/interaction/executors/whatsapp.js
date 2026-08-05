import {
    validateWhatsAppRecipient,
    whatsappUrl,
} from "../validators.js";

export function executeWhatsApp(context) {
    const validation =
        validateWhatsAppRecipient(
            context.action.value
        );

    if (!validation.valid) {
        return {
            handled: false,
            status: "invalid",
            type: context.definition.type,
            intent: "OPEN_WHATSAPP",
            reason: validation.code,
            message: validation.message,
            payload: {
                recipient: "",
                message: String(
                    context.action.target || ""
                ),
                url: "",
                openInNewTab: Boolean(
                    context.action.openInNewTab
                ),
            },
        };
    }

    const message = String(
        context.action.target || ""
    ).trim();

    const payload = {
        recipient: validation.value,
        message,
        url: whatsappUrl(
            validation.value,
            message
        ),
        openInNewTab: Boolean(
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
            intent: "OPEN_WHATSAPP",
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
        intent: "OPEN_WHATSAPP",
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
