import { normalizeRenderMode } from "./constants.js";
import { createRenderCanvas, createRenderNode, createRenderResult } from "./render_tree.js";
import {
    resolveUniversalCanvas,
    resolveUniversalChildOrder,
    resolveUniversalNodeStyle,
} from "./universal_style_resolver.js";
import { resolveUniversalInteraction } from "./universal_interaction_resolver.js";

export const UNIVERSAL_RENDERER_VERSION = 1;

export class UniversalRenderer {
    renderDocument(document = {}, options = {}) {
        const context = normalizeContext(options);
        const canvases = [...(document.canvases || [])]
            .filter((canvas) => canvas.visible !== false)
            .sort((a, b) => Number(a.order || 0) - Number(b.order || 0))
            .map((canvas) => this.renderCanvas(canvas, {
                ...context,
                document,
            }));

        return createRenderResult({
            mode: context.mode,
            document,
            canvases,
            metadata: {
                renderer: "UNIVERSAL",
                rendererVersion: UNIVERSAL_RENDERER_VERSION,
                device: context.device,
                editable: context.mode === "EDIT",
                interactive: context.mode !== "EDIT",
                canvasCount: canvases.length,
            },
        });
    }

    renderCanvas(canvas = {}, context = {}) {
        const resolved = resolveUniversalCanvas(canvas, context);
        const children = resolveUniversalChildOrder(canvas.nodes || [])
            .map(({ node, stackIndex }) => this.renderNode(node, {
                ...context,
                canvas,
                parent: canvas,
                stackIndex,
            }))
            .filter(Boolean);

        return createRenderCanvas({
            ...canvas,
            width: resolved.width,
            height: resolved.height,
            style: resolved.style,
        }, children);
    }

    renderNode(node = {}, context = {}) {
        if (!node?.id || node.visible === false) return null;

        const type = String(node.type || "UNKNOWN").toUpperCase();
        const interaction = resolveUniversalInteraction(node, context);
        const children = resolveUniversalChildOrder(node.children || node.nodes || [])
            .map(({ node: child, stackIndex }) => this.renderNode(child, {
                ...context,
                parent: node,
                stackIndex,
            }))
            .filter(Boolean);

        const descriptor = descriptorFor(type, node, interaction);
        return createRenderNode({
            id: node.id,
            type,
            tag: descriptor.tag,
            attributes: {
                "data-node-id": node.id,
                "data-node-type": type,
                "data-render-mode": context.mode,
                "data-stack-index": String(context.stackIndex || 1),
                ...interaction.attributes,
                ...descriptor.attributes,
            },
            style: resolveUniversalNodeStyle(node, context),
            content: descriptor.content,
            children,
            source: node,
            runtime: {
                actionable: interaction.actionable,
                interactionEnabled: interaction.enabled,
                interaction: interaction.contract,
                editable: context.mode === "EDIT",
            },
        });
    }
}

function descriptorFor(type, node, interaction) {
    const content = node.content || {};

    switch (type) {
        case "TEXT":
            return {
                tag: safeTextTag(content.tag),
                content: String(content.text ?? node.text ?? ""),
                attributes: {},
            };
        case "IMAGE":
            return {
                tag: "img",
                content: null,
                attributes: {
                    src: mediaUrl(node),
                    alt: content.alt || interaction.contract.ariaLabel || node.name || "",
                    draggable: false,
                    loading: "lazy",
                },
            };
        case "VIDEO":
            return {
                tag: "video",
                content: null,
                attributes: {
                    src: mediaUrl(node),
                    controls: content.controls !== false,
                    muted: Boolean(content.muted),
                    autoplay: Boolean(content.autoplay),
                    loop: Boolean(content.loop),
                    playsinline: true,
                },
            };
        case "BUTTON":
            return {
                tag: "button",
                content: String(content.label ?? content.text ?? "Botón"),
                attributes: {
                    type: "button",
                    disabled: false,
                },
            };
        case "SEPARATOR":
            return { tag: "hr", content: null, attributes: {} };
        case "LINK":
            return {
                tag: "a",
                content: String(content.text ?? node.name ?? "Enlace"),
                attributes: { href: "#" },
            };
        default:
            return { tag: "div", content: content.text ?? null, attributes: {} };
    }
}

function mediaUrl(node) {
    return String(
        node.content?.url
        || node.content?.source
        || node.asset?.url
        || node.src
        || "",
    );
}

function safeTextTag(value) {
    const tag = String(value || "div").toLowerCase();
    return ["div", "p", "span", "h1", "h2", "h3", "h4", "h5", "h6"].includes(tag)
        ? tag
        : "div";
}

function normalizeContext(options = {}) {
    return {
        mode: normalizeRenderMode(options.mode || "EDIT"),
        device: ["mobile", "tablet", "desktop"].includes(options.device)
            ? options.device
            : "mobile",
        bindings: options.bindings || {},
        runtime: options.runtime || {},
    };
}
