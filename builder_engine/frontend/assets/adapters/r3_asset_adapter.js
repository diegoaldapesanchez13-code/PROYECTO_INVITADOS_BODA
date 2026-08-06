import { ASSET_SOURCES, ASSET_TYPES } from "../constants.js";
import { normalizeAsset } from "../asset_schema.js";

export function r3AssetToEngine(raw = {}) {
    return normalizeAsset({
        id: raw.id,
        backendId: raw.backendId ?? raw.id,
        type: mapType(raw.type, raw.mimeType),
        source: mapSource(raw.source),
        name: raw.name || raw.title,
        url: raw.url || raw.src,
        previewUrl: raw.previewUrl || raw.thumbnailUrl || raw.url || raw.src,
        mimeType: raw.mimeType,
        size: raw.size || raw.metadata?.size,
        width: raw.width || raw.metadata?.width,
        height: raw.height || raw.metadata?.height,
        duration: raw.duration || raw.metadata?.duration,
        category: raw.category,
        tags: raw.tags,
        metadata: raw.metadata,
    });
}

export function engineAssetToR3(asset = {}) {
    const normalized = normalizeAsset(asset);
    return {
        id: normalized.id,
        backendId: normalized.backendId,
        type: normalized.type,
        source: normalized.source,
        name: normalized.name,
        url: normalized.url,
        previewUrl: normalized.previewUrl,
        mimeType: normalized.mimeType,
        size: normalized.size,
        metadata: {
            ...normalized.metadata,
            width: normalized.width,
            height: normalized.height,
            duration: normalized.duration,
        },
    };
}

export function r3AssetsToEngine(assets = []) {
    return Array.isArray(assets) ? assets.map(r3AssetToEngine) : [];
}

function mapType(type, mimeType = "") {
    const value = String(type || "").toUpperCase();
    if (Object.values(ASSET_TYPES).includes(value)) return value;
    if (String(mimeType).startsWith("video/")) return ASSET_TYPES.VIDEO;
    if (String(mimeType).startsWith("audio/")) return ASSET_TYPES.AUDIO;
    return ASSET_TYPES.IMAGE;
}
function mapSource(source) {
    const value = String(source || "").toUpperCase();
    return Object.values(ASSET_SOURCES).includes(value) ? value : ASSET_SOURCES.UPLOAD;
}
