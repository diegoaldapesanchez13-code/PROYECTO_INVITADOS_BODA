import {
    COMPONENT_CAPABILITIES,
    LAYOUT_MODES,
    componentSupports,
} from "../core/index.js?v=phase-f3-canvas-contract";

export class AutoLayoutEngine {
    constructor({ state, renderer, canvas = null, onLayout = null }) {
        if (!state || !renderer) {
            throw new Error("AutoLayoutEngine requiere state y renderer.");
        }
        this.state = state;
        this.renderer = renderer;
        this.canvas = canvas;
        this.onLayout = onLayout;
    }

    applyAll() {
        const document = this.state.document;
        const nodes = [
            ...canvasesOf(document),
            ...nodesOf(document),
        ]
            .filter((node) => componentSupports(
                node.type,
                COMPONENT_CAPABILITIES.AUTO_LAYOUT
            ))
            .sort((a, b) => this.depth(b.id) - this.depth(a.id));

        let changed = false;

        this.state.transaction("layout:apply-all", () => {
            for (const node of nodes) {
                changed = this.applyToNode(node.id, { render: false }) || changed;
            }
        });

        if (changed) {
            this.renderer.update(this.state.document);
            this.canvas?.refreshAfterRender?.();
        }

        this.onLayout?.({ changed, scope: "all" });
        return changed;
    }

    applyToNode(nodeId, { render = true } = {}) {
        const parent = this.state.getNode(nodeId);
        if (
            !parent
            || !componentSupports(
                parent.type,
                COMPONENT_CAPABILITIES.AUTO_LAYOUT
            )
        ) return false;

        const children = this.state.getChildren(parent.id)
            .filter((node) => node.visible && node.layoutMode === LAYOUT_MODES.FLOW);

        if (!children.length) return false;

        const style = parent.style || {};
        const direction = style.direction === "row" ? "row" : "column";
        const gap = number(style.gap, 0);
        const paddingX = number(style.paddingX, 0);
        const paddingY = number(style.paddingY, 0);

        const patches = direction === "row"
            ? rowLayout(parent, children, { gap, paddingX, paddingY, wrap: Boolean(style.wrap) })
            : columnLayout(parent, children, { gap, paddingX, paddingY });

        let changed = false;

        for (const [childId, patch] of patches.entries()) {
            const current = this.state.getNode(childId);
            if (!same(current, patch)) {
                this.state.updateNode(childId, patch, { ignoreLock: true });
                changed = true;
            }
        }

        const sizePatch = hugPatch(parent, patches);
        if (sizePatch && !same(parent, sizePatch)) {
            this.state.updateNode(parent.id, sizePatch, { ignoreLock: true });
            changed = true;
        }

        if (render && changed) {
            this.renderer.update(this.state.document);
            this.canvas?.refreshAfterRender?.();
        }

        this.onLayout?.({ changed, scope: "node", nodeId });
        return changed;
    }

    depth(nodeId) {
        let depth = 0;
        let node = this.state.getNode(nodeId);
        while (node?.parentId) {
            depth += 1;
            node = this.state.getNode(node.parentId);
        }
        return depth;
    }
}

function columnLayout(parent, children, { gap, paddingX, paddingY }) {
    const result = new Map();
    const parentHeight = numeric(parent.height, 100);
    let cursor = pxPercent(paddingY, parentHeight);

    children.forEach((child, index) => {
        const width = childSize(child, "x", 100);
        const height = childSize(child, "y", 12);

        result.set(child.id, {
            layoutMode: LAYOUT_MODES.FLOW,
            x: 50,
            y: cursor + height / 2,
            width,
            height,
        });

        cursor += height;
        if (index < children.length - 1) cursor += pxPercent(gap, parentHeight);
    });

    return result;
}

function rowLayout(parent, children, { gap, paddingX, paddingY, wrap }) {
    const result = new Map();
    const parentWidth = numeric(parent.width, 100);
    const parentHeight = numeric(parent.height, 100);
    const left = pxPercent(paddingX, parentWidth);
    const right = 100 - left;
    let x = left;
    let y = pxPercent(paddingY, parentHeight);
    let rowHeight = 0;

    for (const child of children) {
        const width = childSize(child, "x", 20);
        const height = childSize(child, "y", 12);

        if (wrap && x + width > right && x > left) {
            x = left;
            y += rowHeight + pxPercent(gap, parentHeight);
            rowHeight = 0;
        }

        result.set(child.id, {
            layoutMode: LAYOUT_MODES.FLOW,
            x: x + width / 2,
            y: y + height / 2,
            width,
            height,
        });

        x += width + pxPercent(gap, parentWidth);
        rowHeight = Math.max(rowHeight, height);
    }

    return result;
}

function childSize(child, axis, fallback) {
    const style = child.style || {};
    const mode = axis === "x" ? style.sizingX : style.sizingY;
    const value = axis === "x" ? child.width : child.height;
    const hugValue = axis === "x" ? style.hugWidth : style.hugHeight;

    if (mode === "fill") return 100;
    if (mode === "hug") return clamp(numeric(hugValue, numeric(value, fallback)), 1, 200);
    return clamp(numeric(value, fallback), 1, 200);
}

function hugPatch(parent, patches) {
    const style = parent.style || {};
    if (style.sizingX !== "hug" && style.sizingY !== "hug") return null;

    const values = [...patches.values()];
    const minX = Math.min(...values.map((v) => v.x - v.width / 2));
    const maxX = Math.max(...values.map((v) => v.x + v.width / 2));
    const minY = Math.min(...values.map((v) => v.y - v.height / 2));
    const maxY = Math.max(...values.map((v) => v.y + v.height / 2));
    const patch = {};

    if (style.sizingX === "hug") patch.width = clamp(maxX - minX, 1, 200);
    if (style.sizingY === "hug") patch.height = clamp(maxY - minY, 1, 200);

    return patch;
}

function same(current, patch) {
    return Object.entries(patch).every(([key, value]) => current[key] === value);
}
function numeric(value, fallback) {
    if (value === "auto") return fallback;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function pxPercent(px, base) {
    return (Number(px || 0) / Math.max(Number(base || 1), 1)) * 100;
}
function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function canvasesOf(document) {
    return Array.isArray(document?.canvases)
        ? document.canvases
        : [];
}

function nodesOf(document) {
    return Array.isArray(document?.nodes)
        ? document.nodes
        : [];
}
