import { createRenderNode } from "./render_tree.js";

function baseNode(node, context, overrides = {}) {
    return createRenderNode({
        id: node.id,
        type: node.type,
        tag: overrides.tag || "div",
        attributes: {
            "data-node-id": node.id,
            "data-node-type": node.type,
            "data-render-mode": context.mode,
            ...(overrides.attributes || {}),
        },
        style: { ...(node.style || {}), ...(overrides.style || {}) },
        content: overrides.content ?? node.content ?? null,
        children: overrides.children || [],
        source: node,
        runtime: overrides.runtime || null,
    });
}

export function renderText(node, context) {
    const text = node.content?.text ?? node.text ?? "";
    return baseNode(node, context, { tag: "div", content: String(text) });
}

export function renderImage(node, context) {
    const src = node.asset?.url || node.content?.src || node.src || "";
    return baseNode(node, context, {
        tag: "img",
        attributes: { src, alt: node.content?.alt || node.name || "" },
    });
}

export function renderContainer(node, context, children) {
    return baseNode(node, context, { tag: "div", children });
}

export function renderButton(node, context, children) {
    return baseNode(node, context, {
        tag: "button",
        attributes: { type: "button", disabled: context.mode === "EDIT" },
        content: node.content?.text ?? node.text ?? "Botón",
        children,
    });
}

export function renderUnknown(node, context, children) {
    return baseNode(node, context, { tag: "div", children });
}

export function registerDefaultRenderers(registry) {
    registry.register("TEXT", renderText, { replace: true });
    registry.register("IMAGE", renderImage, { replace: true });
    registry.register("BUTTON", renderButton, { replace: true });
    for (const type of ["CARD", "CONTAINER", "GROUP", "COUNTDOWN", "SECTION"]) {
        registry.register(type, renderContainer, { replace: true });
    }
    registry.registerFallback(renderUnknown);
    return registry;
}
