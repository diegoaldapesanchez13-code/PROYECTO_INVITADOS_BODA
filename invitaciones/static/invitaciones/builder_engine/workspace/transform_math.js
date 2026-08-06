export const DEVICE_PROFILES = Object.freeze({
    mobile: Object.freeze({ key: "mobile", width: 390, label: "iPhone" }),
    tablet: Object.freeze({ key: "tablet", width: 768, label: "Tablet" }),
    desktop: Object.freeze({ key: "desktop", width: 1180, label: "Desktop" }),
});

export function pixelsToPercent(deltaPixels, referencePixels) {
    const reference = Number(referencePixels);
    if (!Number.isFinite(reference) || reference <= 0) return 0;
    return (Number(deltaPixels || 0) / reference) * 100;
}

export function dragTransform(initial, delta, bounds, options = {}) {
    const snap = Number(options.snap || 0);
    const x = Number(initial.x ?? 50) + pixelsToPercent(delta.x, bounds.width);
    const y = Number(initial.y ?? 50) + pixelsToPercent(delta.y, bounds.height);
    return {
        ...initial,
        x: clamp(applySnap(x, snap), options.minX ?? -100, options.maxX ?? 200),
        y: clamp(applySnap(y, snap), options.minY ?? -100, options.maxY ?? 200),
    };
}

export function resizeTransform(initial, delta, bounds, handle = "se", options = {}) {
    const widthDelta = pixelsToPercent(delta.x, bounds.width);
    const minWidth = Number(options.minWidth ?? 2);
    const maxWidth = Number(options.maxWidth ?? 300);
    let width = Number(initial.width ?? 50);
    let x = Number(initial.x ?? 50);

    if (handle.includes("e")) width += widthDelta;
    if (handle.includes("w")) {
        width -= widthDelta;
        x += widthDelta / 2;
    }
    if (handle.includes("e")) x += widthDelta / 2;

    return {
        ...initial,
        width: clamp(width, minWidth, maxWidth),
        x,
    };
}

export function rotationFromPoints(center, start, current, initialRotation = 0, options = {}) {
    const startAngle = Math.atan2(start.y - center.y, start.x - center.x);
    const currentAngle = Math.atan2(current.y - center.y, current.x - center.x);
    let degrees = Number(initialRotation || 0) + ((currentAngle - startAngle) * 180 / Math.PI);
    const snap = options.snap === false ? 0 : Number(options.snap || 15);
    if (snap > 0 && options.shiftKey) degrees = Math.round(degrees / snap) * snap;
    return normalizeDegrees(degrees);
}

export function resolveResponsiveStyle(style = {}, device = "mobile") {
    const base = { ...style };
    delete base.responsive;
    const override = style.responsive?.[device];
    return override && typeof override === "object"
        ? { ...base, ...override }
        : base;
}

export function writeResponsiveStyle(style = {}, patch = {}, device = "mobile", options = {}) {
    if (options.base === true) return { ...style, ...patch };
    return {
        ...style,
        responsive: {
            ...(style.responsive || {}),
            [device]: {
                ...(style.responsive?.[device] || {}),
                ...patch,
            },
        },
    };
}

function applySnap(value, snap) {
    return snap > 0 ? Math.round(value / snap) * snap : value;
}

function clamp(value, min, max) {
    return Math.min(Math.max(Number(value), Number(min)), Number(max));
}

function normalizeDegrees(value) {
    let result = Number(value) % 360;
    if (result > 180) result -= 360;
    if (result < -180) result += 360;
    return result;
}
