export const CANVAS_SIZE_CONTRACT_VERSION = 1;

export const CANVAS_DEVICE_PROFILES = Object.freeze({
    mobile: Object.freeze({ width: 390, defaultHeight: 844 }),
    tablet: Object.freeze({ width: 768, defaultHeight: 960 }),
    desktop: Object.freeze({ width: 1180, defaultHeight: 820 }),
});

export const CANVAS_HEIGHT_MODES = Object.freeze({
    FIXED: "FIXED",
    AUTO: "AUTO",
});

export function createCanvasSizeContract(raw = {}) {
    const responsive = object(raw.responsive);

    return {
        contractVersion: CANVAS_SIZE_CONTRACT_VERSION,
        baseDevice: "mobile",
        heightMode: enumValue(
            raw.heightMode,
            Object.values(CANVAS_HEIGHT_MODES),
            CANVAS_HEIGHT_MODES.FIXED,
        ),
        minHeight: positive(raw.minHeight, 240),
        maxHeight: positive(raw.maxHeight, 6000),
        overflow: String(raw.overflow || "hidden").toLowerCase(),
        responsive: {
            mobile: normalizeDeviceSize("mobile", responsive.mobile, raw.height),
            tablet: normalizeDeviceSize("tablet", responsive.tablet),
            desktop: normalizeDeviceSize("desktop", responsive.desktop),
        },
    };
}

export function resolveCanvasSize(contract, device = "mobile") {
    const normalized = createCanvasSizeContract(contract);
    const key = CANVAS_DEVICE_PROFILES[device] ? device : "mobile";
    const mobile = normalized.responsive.mobile;
    const current = normalized.responsive[key];

    return {
        width: CANVAS_DEVICE_PROFILES[key].width,
        height: current.height ?? mobile.height,
        heightMode: current.heightMode || normalized.heightMode,
        minHeight: normalized.minHeight,
        maxHeight: normalized.maxHeight,
        overflow: normalized.overflow,
    };
}

export function writeCanvasHeight(contract, device, height) {
    const normalized = createCanvasSizeContract(contract);
    const key = CANVAS_DEVICE_PROFILES[device] ? device : "mobile";
    const safeHeight = clamp(
        height,
        normalized.minHeight,
        normalized.maxHeight,
        CANVAS_DEVICE_PROFILES[key].defaultHeight,
    );

    return {
        ...normalized,
        responsive: {
            ...normalized.responsive,
            [key]: {
                ...normalized.responsive[key],
                height: safeHeight,
                heightMode: CANVAS_HEIGHT_MODES.FIXED,
            },
        },
    };
}

export function validateCanvasSizeContract(value) {
    const errors = [];
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return { valid: false, errors: ["CanvasSize debe ser un objeto."] };
    }

    const normalized = createCanvasSizeContract(value);
    if (normalized.minHeight > normalized.maxHeight) {
        errors.push("minHeight no puede superar maxHeight.");
    }

    for (const [device, size] of Object.entries(normalized.responsive)) {
        if (size.width !== CANVAS_DEVICE_PROFILES[device].width) {
            errors.push(`El ancho de ${device} debe ser fijo.`);
        }
    }

    return { valid: errors.length === 0, errors, value: normalized };
}

function normalizeDeviceSize(device, raw = {}, fallbackHeight = null) {
    const profile = CANVAS_DEVICE_PROFILES[device];
    const source = object(raw);
    const providedHeight = source.height ?? fallbackHeight;

    return {
        width: profile.width,
        height: providedHeight == null
            ? (device === "mobile" ? profile.defaultHeight : null)
            : positive(providedHeight, profile.defaultHeight),
        heightMode: enumValue(
            source.heightMode,
            Object.values(CANVAS_HEIGHT_MODES),
            CANVAS_HEIGHT_MODES.FIXED,
        ),
    };
}

function object(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function enumValue(value, allowed, fallback) {
    const normalized = String(value || "").toUpperCase();
    return allowed.includes(normalized) ? normalized : fallback;
}

function positive(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function clamp(value, min, max, fallback) {
    const parsed = Number(value);
    const safe = Number.isFinite(parsed) ? parsed : fallback;
    return Math.min(Math.max(safe, min), max);
}
