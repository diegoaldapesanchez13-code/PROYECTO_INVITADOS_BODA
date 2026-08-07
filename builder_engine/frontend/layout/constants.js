export const LAYOUT_CONTRACT_VERSION = 1;

export const LAYOUT_MODES = Object.freeze({
    LAYER: "LAYER",
    FLOW: "FLOW",
});

export const COORDINATE_SPACES = Object.freeze({
    CANVAS: "CANVAS",
    PARENT: "PARENT",
});

export const TRANSFORM_ORIGINS = Object.freeze({
    CENTER: Object.freeze({ x: 0.5, y: 0.5 }),
    TOP_LEFT: Object.freeze({ x: 0, y: 0 }),
});

export const DEVICE_KEYS = Object.freeze({
    MOBILE: "mobile",
    TABLET: "tablet",
    DESKTOP: "desktop",
});

export const DEVICE_ORDER = Object.freeze([
    DEVICE_KEYS.MOBILE,
    DEVICE_KEYS.TABLET,
    DEVICE_KEYS.DESKTOP,
]);
