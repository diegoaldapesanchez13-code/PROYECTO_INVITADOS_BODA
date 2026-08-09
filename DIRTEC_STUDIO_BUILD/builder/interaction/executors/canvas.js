export function executeCanvas(context) {
    const canvasId = String(
        context.action.value
        || context.action.target
        || ""
    ).trim();

    if (!canvasId) {
        return invalid(
            "canvas-id-required",
            "Selecciona un lienzo de destino.",
            canvasId
        );
    }

    const hasDocumentCanvass = Array.isArray(
        context.document?.canvases
    );

    const canvass = hasDocumentCanvass
        ? context.document.canvases
        : [];

    const exists = canvass.some(
        (canvas) =>
            canvas.id === canvasId
    );

    if (hasDocumentCanvass && !exists) {
        return invalid(
            "canvas-not-found",
            "El lienzo de destino ya no existe.",
            canvasId
        );
    }

    const payload = {
        canvasId,
        behavior: "smooth",
        block: "start",
    };

    const runtime = context.runtime;

    if (
        !runtime
        || typeof runtime.navigateCanvas
            !== "function"
    ) {
        return {
            handled: true,
            status: "ready",
            type: context.definition.type,
            intent: "NAVIGATE_CANVAS",
            payload,
            runtime: {
                executed: false,
                reason: "runtime-unavailable",
            },
        };
    }

    const runtimeResult =
        runtime.navigateCanvas(
            canvasId,
            {
                behavior: payload.behavior,
                block: payload.block,
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
        intent: "NAVIGATE_CANVAS",
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

function invalid(reason, message, canvasId) {
    return {
        handled: false,
        status: "invalid",
        type: "CANVAS",
        intent: "NAVIGATE_CANVAS",
        reason,
        message,
        payload: {
            canvasId,
            behavior: "smooth",
            block: "start",
        },
    };
}
