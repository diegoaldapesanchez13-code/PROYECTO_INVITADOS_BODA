export const ASSETS_MODULE_KEY = "assets";

export const ASSET_TYPES = Object.freeze({
    IMAGE: "IMAGE",
    VIDEO: "VIDEO",
    AUDIO: "AUDIO",
    ICON: "ICON",
    DOCUMENT: "DOCUMENT",
    OTHER: "OTHER",
});

export const ASSET_SOURCES = Object.freeze({
    UPLOAD: "UPLOAD",
    BUILTIN: "BUILTIN",
    REMOTE: "REMOTE",
});

export const FORBIDDEN_PERSISTENT_URL_SCHEMES = Object.freeze([
    "data:",
    "blob:",
]);
