import { resolveCanvasSize } from "../canvas/canvas_size_contract.js";
import { createTransformContract, resolveTransform } from "../layout/transform_contract.js";

const UNITLESS = new Set([
    "opacity", "zIndex", "fontWeight", "lineHeight", "flexGrow",
    "flexShrink", "order",
]);

export function resolveUniversalCanvas(canvas = {}, context = {}) {
    const device = normalizeDevice(context.device);
    const size = resolveCanvasSize(
        canvas.size || {
            height: canvas.height,
            minHeight: canvas.minHeight,
            maxHeight: canvas.maxHeight,
            overflow: canvas.style?.overflow,
        },
        device,
    );

    return {
        width: size.width,
        height: size.height,
        style: {
            position: "relative",
            width: `${size.width}px`,
            height: `${size.height}px`,
            minHeight: `${size.minHeight}px`,
            maxHeight: `${size.maxHeight}px`,
            overflow: size.overflow,
            boxSizing: "border-box",
            isolation: "isolate",
            ...resolveBackground(canvas.background || canvas.style?.background),
        },
    };
}

export function resolveUniversalNodeStyle(node = {}, context = {}) {
    const device = normalizeDevice(context.device);
    const layout = createTransformContract(
        node.layout || legacyLayoutFromStyle(node.style || {}),
    );
    const transform = resolveTransform(layout, device);
    const visual = node.style || {};
    const layoutMode = layout.layoutMode;

    const style = {
        boxSizing: "border-box",
        opacity: transform.opacity,
        transformOrigin: `${transform.originX * 100}% ${transform.originY * 100}%`,
        transform: `rotate(${transform.rotation}deg)`,
        zIndex: Number(context.stackIndex || visual.zIndex || 1),
    };

    if (layoutMode === "FLOW") {
        Object.assign(style, {
            position: "relative",
            width: percent(transform.width),
            minHeight: percent(transform.height),
        });
    } else {
        Object.assign(style, {
            position: "absolute",
            left: percent(transform.x),
            top: percent(transform.y),
            width: percent(transform.width),
            height: percent(transform.height),
            translate: `${-transform.originX * 100}% ${-transform.originY * 100}%`,
        });
    }

    applyVisualStyle(style, visual, node.type);
    return style;
}

export function resolveUniversalChildOrder(nodes = []) {
    return [...nodes]
        .filter(Boolean)
        .map((node, sourceIndex) => ({
            node,
            sourceIndex,
            zIndex: Number(node.style?.zIndex || sourceIndex + 1),
        }))
        .sort((a, b) => {
            const byZ = a.zIndex - b.zIndex;
            return byZ || a.sourceIndex - b.sourceIndex;
        })
        .map((entry, index) => ({
            node: entry.node,
            stackIndex: index + 1,
        }));
}

export function styleToCssObject(style = {}) {
    const result = {};
    for (const [key, value] of Object.entries(style)) {
        if (value === undefined || value === null || value === "") continue;
        result[key] = typeof value === "number" && !UNITLESS.has(key)
            ? `${value}px`
            : String(value);
    }
    return result;
}

function legacyLayoutFromStyle(style) {
    return {
        transform: {
            x: style.x,
            y: style.y,
            width: style.width,
            height: style.height,
            rotation: style.rotation,
            opacity: style.opacity,
            originX: style.originX,
            originY: style.originY,
        },
        responsive: style.responsive,
        constraints: {
            aspectRatio: style.aspectRatio,
            lockAspectRatio: style.lockAspectRatio,
        },
    };
}

function applyVisualStyle(target, source, type) {
    const properties = [
        "color", "backgroundColor", "borderColor", "borderStyle", "borderWidth",
        "borderRadius", "boxShadow", "fontFamily", "fontSize", "fontWeight",
        "fontStyle", "lineHeight", "letterSpacing", "textAlign", "textTransform",
        "textDecoration", "padding", "paddingTop", "paddingRight", "paddingBottom",
        "paddingLeft", "margin", "gap", "display", "flexDirection",
        "justifyContent", "alignItems", "objectFit", "objectPosition", "overflow",
        "cursor", "pointerEvents", "whiteSpace", "wordBreak",
    ];

    for (const property of properties) {
        if (source[property] !== undefined && source[property] !== null) {
            target[property] = normalizeVisualValue(property, source[property]);
        }
    }

    const normalizedType = String(type || "").toUpperCase();
    if (["IMAGE", "VIDEO"].includes(normalizedType)) {
        target.display = source.display || "block";
        target.objectFit = source.fit || source.objectFit || "cover";
        target.width = target.width || "100%";
        target.height = target.height || "100%";
    }

    if (normalizedType === "BUTTON") {
        target.display = source.display || "flex";
        target.alignItems = source.alignItems || "center";
        target.justifyContent = source.justifyContent || "center";
    }

    if (["CONTAINER", "CARD", "GROUP", "COUNTDOWN"].includes(normalizedType)) {
        target.display = source.display || "flex";
        target.flexDirection = source.direction || source.flexDirection || "column";
    }
}

function normalizeVisualValue(property, value) {
    if (typeof value !== "number") return value;
    if (UNITLESS.has(property)) return value;
    if (["fontSize", "letterSpacing", "borderWidth", "borderRadius", "padding",
        "paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "margin",
        "gap"].includes(property)) {
        return `${value}px`;
    }
    return value;
}

function resolveBackground(background = {}) {
    if (typeof background === "string") {
        return { background };
    }

    const style = {};
    if (background.color) style.backgroundColor = background.color;
    if (background.url) {
        style.backgroundImage = `url("${background.url}")`;
        style.backgroundSize = background.size || "cover";
        style.backgroundPosition = background.position || "center";
        style.backgroundRepeat = background.repeat || "no-repeat";
    }
    return style;
}

function percent(value) {
    return `${Number(value || 0)}%`;
}

function normalizeDevice(value) {
    return ["mobile", "tablet", "desktop"].includes(value) ? value : "mobile";
}
