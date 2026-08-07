export function executeSection(context) {
    const sectionId = String(
        context.action.value
        || context.action.target
        || ""
    ).trim();

    if (!sectionId) {
        return invalid(
            "section-id-required",
            "Selecciona un lienzo de destino.",
            sectionId
        );
    }

    const hasDocumentSections = Array.isArray(
        context.document?.sections
    );

    const sections = hasDocumentSections
        ? context.document.sections
        : [];

    const exists = sections.some(
        (section) =>
            section.id === sectionId
    );

    if (hasDocumentSections && !exists) {
        return invalid(
            "section-not-found",
            "El lienzo de destino ya no existe.",
            sectionId
        );
    }

    const payload = {
        sectionId,
        behavior: "smooth",
        block: "start",
    };

    const runtime = context.runtime;

    if (
        !runtime
        || typeof runtime.navigateSection
            !== "function"
    ) {
        return {
            handled: true,
            status: "ready",
            type: context.definition.type,
            intent: "NAVIGATE_SECTION",
            payload,
            runtime: {
                executed: false,
                reason: "runtime-unavailable",
            },
        };
    }

    const runtimeResult =
        runtime.navigateSection(
            sectionId,
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
        intent: "NAVIGATE_SECTION",
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

function invalid(reason, message, sectionId) {
    return {
        handled: false,
        status: "invalid",
        type: "SECTION",
        intent: "NAVIGATE_SECTION",
        reason,
        message,
        payload: {
            sectionId,
            behavior: "smooth",
            block: "start",
        },
    };
}
