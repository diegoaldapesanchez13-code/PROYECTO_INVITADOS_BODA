import {
    COORDINATE_SPACES,
    DEVICE_KEYS,
    LAYOUT_CONTRACT_VERSION,
    LAYOUT_MODES,
    TRANSFORM_ORIGINS,
} from "./constants.js";

export function createTransformContract(raw = {}) {
    const transformSource = object(raw.transform);
    const responsiveSource = object(raw.responsive);

    return {
        contractVersion: LAYOUT_CONTRACT_VERSION,
        layoutMode: enumValue(
            raw.layoutMode,
            Object.values(LAYOUT_MODES),
            LAYOUT_MODES.LAYER,
        ),
        coordinateSpace: enumValue(
            raw.coordinateSpace,
            Object.values(COORDINATE_SPACES),
            COORDINATE_SPACES.PARENT,
        ),
        transform: normalizeTransform(transformSource),
        responsive: {
            mobile: normalizeTransformOverride(responsiveSource.mobile),
            tablet: normalizeTransformOverride(responsiveSource.tablet),
            desktop: normalizeTransformOverride(responsiveSource.desktop),
        },
        constraints: normalizeConstraints(raw.constraints),
    };
}

export function normalizeTransform(raw = {}) {
    return {
        x: finite(raw.x, 50),
        y: finite(raw.y, 50),
        width: positive(raw.width, 50),
        height: positive(raw.height, 12),
        rotation: finite(raw.rotation, 0),
        opacity: clamp(raw.opacity, 0, 1, 1),
        originX: clamp(raw.originX, 0, 1, TRANSFORM_ORIGINS.CENTER.x),
        originY: clamp(raw.originY, 0, 1, TRANSFORM_ORIGINS.CENTER.y),
    };
}

export function resolveTransform(contract, device = DEVICE_KEYS.MOBILE) {
    const normalized = createTransformContract(contract);
    const key = Object.values(DEVICE_KEYS).includes(device)
        ? device
        : DEVICE_KEYS.MOBILE;

    return {
        ...normalized.transform,
        ...normalized.responsive[key],
    };
}

export function writeTransformOverride(contract, patch, device = DEVICE_KEYS.MOBILE) {
    const normalized = createTransformContract(contract);
    const cleanPatch = normalizeTransformOverride(patch);

    return {
        ...normalized,
        responsive: {
            ...normalized.responsive,
            [device]: {
                ...normalized.responsive[device],
                ...cleanPatch,
            },
        },
    };
}

export function writeBaseTransform(contract, patch) {
    const normalized = createTransformContract(contract);
    return {
        ...normalized,
        transform: normalizeTransform({
            ...normalized.transform,
            ...object(patch),
        }),
    };
}

export function validateTransformContract(value) {
    const errors = [];
    if (!value || typeof value !== "object" || Array.isArray(value)) {
        return { valid: false, errors: ["El contrato de transformación debe ser un objeto."] };
    }

    const normalized = createTransformContract(value);
    if (normalized.transform.width <= 0) errors.push("width debe ser positivo.");
    if (normalized.transform.height <= 0) errors.push("height debe ser positivo.");
    if (
        normalized.layoutMode === LAYOUT_MODES.FLOW
        && normalized.coordinateSpace === COORDINATE_SPACES.CANVAS
    ) {
        errors.push("Un nodo FLOW no debe usar coordenadas absolutas de CANVAS.");
    }

    return { valid: errors.length === 0, errors, value: normalized };
}

function normalizeTransformOverride(raw = {}) {
    const source = object(raw);
    const result = {};

    for (const key of [
        "x", "y", "width", "height", "rotation",
        "opacity", "originX", "originY",
    ]) {
        if (source[key] == null || source[key] === "") continue;
        const value = Number(source[key]);
        if (Number.isFinite(value)) result[key] = value;
    }

    // zIndex deliberately does not belong to responsive geometry.
    return result;
}

function normalizeConstraints(raw = {}) {
    const source = object(raw);
    return {
        minWidth: positive(source.minWidth, 1),
        minHeight: positive(source.minHeight, 1),
        maxWidth: positive(source.maxWidth, 300),
        maxHeight: positive(source.maxHeight, 600),
        lockAspectRatio: Boolean(source.lockAspectRatio),
        aspectRatio: positiveOrNull(source.aspectRatio),
        allowMove: source.allowMove !== false,
        allowResize: source.allowResize !== false,
        allowRotate: source.allowRotate !== false,
    };
}

function enumValue(value, allowed, fallback) {
    const normalized = String(value || "").toUpperCase();
    return allowed.includes(normalized) ? normalized : fallback;
}

function object(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function finite(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function positive(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function positiveOrNull(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function clamp(value, min, max, fallback) {
    const parsed = Number(value);
    const safe = Number.isFinite(parsed) ? parsed : fallback;
    return Math.min(Math.max(safe, min), max);
}
