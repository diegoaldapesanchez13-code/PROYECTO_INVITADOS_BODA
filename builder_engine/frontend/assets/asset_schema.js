import { ASSET_SOURCES, ASSET_TYPES, FORBIDDEN_PERSISTENT_URL_SCHEMES } from "./constants.js";

export function normalizeAsset(raw = {}) {
    const source = raw && typeof raw === "object" ? raw : {};
    const now = new Date().toISOString();
    const url = String(source.url || "").trim();
    const previewUrl = String(source.previewUrl || url).trim();

    return {
        id: String(source.id || createAssetId()),
        type: normalizeEnum(source.type, ASSET_TYPES, inferType(source.mimeType, url)),
        source: normalizeEnum(source.source, ASSET_SOURCES, ASSET_SOURCES.UPLOAD),
        name: String(source.name || source.originalName || "Recurso"),
        url,
        previewUrl,
        mimeType: String(source.mimeType || inferMimeType(url)),
        storageKey: source.storageKey ? String(source.storageKey) : null,
        backendId: source.backendId ?? source.id ?? null,
        size: finite(source.size, 0),
        width: finite(source.width ?? source.metadata?.width, 0),
        height: finite(source.height ?? source.metadata?.height, 0),
        duration: finite(source.duration ?? source.metadata?.duration, 0),
        category: String(source.category || "General"),
        tags: Array.isArray(source.tags) ? [...new Set(source.tags.map(String))] : [],
        metadata: cloneObject(source.metadata),
        createdAt: String(source.createdAt || now),
        updatedAt: String(source.updatedAt || now),
    };
}

export function validateAsset(asset, options = {}) {
    const errors = [];
    if (!asset || typeof asset !== "object" || Array.isArray(asset)) {
        return { valid: false, errors: ["El asset debe ser un objeto."] };
    }
    if (!String(asset.id || "").trim()) errors.push("id es obligatorio.");
    if (!Object.values(ASSET_TYPES).includes(asset.type)) errors.push("type no es válido.");
    if (!Object.values(ASSET_SOURCES).includes(asset.source)) errors.push("source no es válido.");
    const requirePersistentUrl = options.requirePersistentUrl !== false;
    if (requirePersistentUrl && isTransientAssetUrl(asset.url)) {
        errors.push("url no puede usar data: ni blob: en un documento persistente.");
    }
    if (requirePersistentUrl && asset.source === ASSET_SOURCES.UPLOAD && !String(asset.url || "").trim()) {
        errors.push("Los assets subidos requieren una URL persistente.");
    }
    return { valid: errors.length === 0, errors };
}

export function isTransientAssetUrl(url = "") {
    const value = String(url).trim().toLowerCase();
    return FORBIDDEN_PERSISTENT_URL_SCHEMES.some((scheme) => value.startsWith(scheme));
}

export function sanitizeAssetForDocument(raw = {}) {
    const asset = normalizeAsset(raw);
    if (isTransientAssetUrl(asset.url) || isTransientAssetUrl(asset.previewUrl)) {
        throw new Error(`El asset "${asset.name}" usa una URL temporal o Base64.`);
    }
    return asset;
}

function normalizeEnum(value, enumeration, fallback) {
    return Object.values(enumeration).includes(value) ? value : fallback;
}
function inferType(mimeType = "", url = "") {
    const mime = String(mimeType).toLowerCase();
    const path = String(url).toLowerCase();
    if (mime.startsWith("video/") || /\.(mp4|webm|ogg|mov|m4v)(\?|$)/.test(path)) return ASSET_TYPES.VIDEO;
    if (mime.startsWith("audio/") || /\.(mp3|wav|ogg|m4a|aac)(\?|$)/.test(path)) return ASSET_TYPES.AUDIO;
    if (mime.startsWith("image/") || /\.(png|jpe?g|webp|gif|svg)(\?|$)/.test(path)) return ASSET_TYPES.IMAGE;
    return ASSET_TYPES.OTHER;
}
function inferMimeType(url = "") {
    const path = String(url).toLowerCase();
    const map = [
        [/\.png(\?|$)/, "image/png"], [/\.webp(\?|$)/, "image/webp"], [/\.gif(\?|$)/, "image/gif"],
        [/\.svg(\?|$)/, "image/svg+xml"], [/\.jpe?g(\?|$)/, "image/jpeg"], [/\.mp4(\?|$)/, "video/mp4"],
        [/\.webm(\?|$)/, "video/webm"], [/\.mp3(\?|$)/, "audio/mpeg"], [/\.wav(\?|$)/, "audio/wav"],
    ];
    return map.find(([pattern]) => pattern.test(path))?.[1] || "application/octet-stream";
}
function createAssetId() {
    if (globalThis.crypto?.randomUUID) return `asset-${globalThis.crypto.randomUUID()}`;
    return `asset-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}
function finite(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}
function cloneObject(value) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return typeof structuredClone === "function" ? structuredClone(value) : JSON.parse(JSON.stringify(value));
}
