/**
 * Envuelve renderers heredados de Builder R3 para utilizarlos desde el contrato
 * headless del nuevo Renderer Engine. El renderer heredado puede devolver un
 * descriptor o un elemento DOM; el adaptador conserva ambos como runtime.
 */
export function adaptR3Renderer(renderer, options = {}) {
    if (typeof renderer !== "function") throw new TypeError("Renderer R3 inválido.");
    return {
        render(node, context, children) {
            const legacyResult = renderer(node, {
                editable: context.mode === "EDIT",
                mode: context.mode.toLowerCase(),
                document: context.document,
                canvas: context.canvas,
                children,
                ...options.context,
            });
            if (legacyResult && typeof legacyResult === "object" && legacyResult.id && legacyResult.type) {
                return legacyResult;
            }
            return {
                id: node.id,
                type: node.type || "UNKNOWN",
                tag: options.tag || "div",
                attributes: {
                    "data-node-id": node.id,
                    "data-r3-adapter": "true",
                },
                style: { ...(node.style || {}) },
                children,
                source: node,
                runtime: { legacyResult },
            };
        },
    };
}

export function registerR3Renderers(registry, definitions = {}) {
    for (const [type, renderer] of Object.entries(definitions)) {
        registry.register(type, adaptR3Renderer(renderer), { replace: true });
    }
    return registry;
}
