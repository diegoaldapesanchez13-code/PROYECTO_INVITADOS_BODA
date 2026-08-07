export function collectLegacyAssets(legacy = {}) {
    const collected = new Map();

    visit(legacy, (candidate) => {
        if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) return;
        const id = candidate.id ?? candidate.assetId ?? candidate.backendId;
        const url = candidate.url || candidate.src || candidate.source;
        if (!id || !url || typeof url !== "string") return;
        const key = String(id);
        if (collected.has(key)) return;

        collected.set(key, {
            id: key,
            backendId: numericOrNull(candidate.backendId ?? candidate.id),
            type: inferType(candidate),
            source: candidate.sourceType === "youtube" ? "YOUTUBE" : "UPLOAD",
            name: String(candidate.title || candidate.name || fileName(url) || `Asset ${key}`),
            url,
            mimeType: String(candidate.mimeType || ""),
            size: Number(candidate.size || 0),
            metadata: {
                legacy: true,
                isVideo: Boolean(candidate.isVideo),
            },
        });
    });

    return [...collected.values()];
}

function visit(value, callback) {
    if (Array.isArray(value)) {
        for (const item of value) visit(item, callback);
        return;
    }
    if (!value || typeof value !== "object") return;
    callback(value);
    for (const item of Object.values(value)) visit(item, callback);
}

function inferType(candidate) {
    if (candidate.isVideo) return "VIDEO";
    const url = String(candidate.url || candidate.src || "").toLowerCase();
    if (/\.(mp4|webm|ogg|mov|m4v)(\?|$)/.test(url)) return "VIDEO";
    if (/\.(mp3|wav|m4a|aac)(\?|$)/.test(url)) return "AUDIO";
    return "IMAGE";
}

function fileName(url) {
    try {
        return decodeURIComponent(String(url).split("?")[0].split("/").pop() || "");
    } catch {
        return "";
    }
}

function numericOrNull(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}
