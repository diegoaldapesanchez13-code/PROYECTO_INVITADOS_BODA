import { createCanvasSizeContract } from "../canvas/canvas_size_contract.js";
import { createNodeInteractionContract } from "../interaction/node_interaction_contract.js";
import { createTransformContract } from "../layout/transform_contract.js";
import { LayerStackService } from "../layers/layer_stack_service.js";

export function migrateDocumentToBaseContracts(document) {
    const next = clone(document || {});
    const stack = new LayerStackService();

    next.canvases = (next.canvases || []).map((canvas) => ({
        ...canvas,
        size: createCanvasSizeContract(
            canvas.size || {
                height: canvas.height,
                minHeight: canvas.minHeight,
                maxHeight: canvas.maxHeight,
                overflow: canvas.style?.overflow,
            },
        ),
        nodes: stack.normalize(
            (canvas.nodes || []).map(migrateNode),
        ),
    }));

    next.globals = {
        ...(next.globals || {}),
        contractMigration: {
            ...((next.globals || {}).contractMigration || {}),
            baseContractsVersion: 1,
        },
    };

    return next;
}

function migrateNode(node = {}) {
    const children = (node.children || []).map(migrateNode);
    const currentStyle = node.style || {};

    const layout = createTransformContract(
        node.layout || {
            layoutMode: node.layoutMode,
            coordinateSpace: node.coordinateSpace,
            transform: {
                x: currentStyle.x,
                y: currentStyle.y,
                width: currentStyle.width,
                height: currentStyle.height,
                rotation: currentStyle.rotation,
                opacity: currentStyle.opacity,
                originX: currentStyle.originX,
                originY: currentStyle.originY,
            },
            responsive: currentStyle.responsive,
            constraints: {
                lockAspectRatio: currentStyle.lockAspectRatio,
                aspectRatio: currentStyle.aspectRatio,
            },
        },
    );

    const interaction = createNodeInteractionContract(
        node.interaction || {
            interactions: node.interactions
                || (node.interaction?.enabled ? [node.interaction] : []),
            states: node.states,
            ariaLabel: node.content?.alt || node.ariaLabel,
        },
    );

    return {
        ...node,
        layout,
        interaction,
        children,
    };
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
