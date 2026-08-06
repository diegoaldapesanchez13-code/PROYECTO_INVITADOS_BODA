const YOUTUBE_HOSTS = new Set([
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
]);

export function normalizeVideoSource(value, options = {}) {
    const sourceType = String(options.sourceType || "auto").toLowerCase();
    const raw = String(value || "").trim();

    if (!raw) return invalid("Agrega una URL o archivo de video.");

    if (sourceType === "youtube" || sourceType === "auto") {
        const youtube = normalizeYouTubeSource(raw, options);
        if (youtube.valid) return youtube;
        if (sourceType === "youtube") return youtube;
    }

    if (sourceType === "direct" || sourceType === "auto") {
        const direct = normalizeDirectVideoSource(raw);
        if (direct.valid) return direct;
        if (sourceType === "direct") return direct;
    }

    return invalid("La fuente no corresponde a YouTube ni a un video directo válido.");
}

export function normalizeYouTubeSource(value, options = {}) {
    const raw = String(value || "").trim();
    let url;

    try {
        url = new URL(raw);
    } catch {
        return invalid("La URL de YouTube no es válida.");
    }

    const host = url.hostname.toLowerCase();
    if (!YOUTUBE_HOSTS.has(host) && !host.endsWith(".youtube.com")) {
        return invalid("La URL no pertenece a YouTube.");
    }

    const videoId = extractYouTubeId(url);
    if (!isYouTubeId(videoId)) {
        return invalid("No se pudo identificar el video de YouTube.");
    }

    const params = new URLSearchParams();
    params.set("rel", "0");
    params.set("playsinline", "1");
    params.set("controls", options.controls === false ? "0" : "1");

    if (options.autoplay) params.set("autoplay", "1");
    if (options.muted !== false) params.set("mute", "1");
    if (options.loop) {
        params.set("loop", "1");
        params.set("playlist", videoId);
    }

    return {
        valid: true,
        kind: "youtube",
        videoId,
        source: raw,
        embedUrl: `https://www.youtube-nocookie.com/embed/${videoId}?${params.toString()}`,
        externalUrl: `https://www.youtube.com/watch?v=${videoId}`,
    };
}

export function normalizeDirectVideoSource(value) {
    const raw = String(value || "").trim();

    if (raw.startsWith("blob:") || raw.startsWith("data:video/")) {
        return {
            valid: true,
            kind: "direct",
            source: raw,
            embedUrl: "",
            externalUrl: raw,
        };
    }

    let url;
    try {
        url = new URL(raw);
    } catch {
        return invalid("La URL del video no es válida.");
    }

    if (!["http:", "https:"].includes(url.protocol)) {
        return invalid("Solo se permiten URLs http o https.");
    }

    return {
        valid: true,
        kind: "direct",
        source: url.toString(),
        embedUrl: "",
        externalUrl: url.toString(),
    };
}

function extractYouTubeId(url) {
    const host = url.hostname.toLowerCase();

    if (host === "youtu.be" || host === "www.youtu.be") {
        return url.pathname.split("/").filter(Boolean)[0] || "";
    }

    const watchId = url.searchParams.get("v");
    if (watchId) return watchId;

    const parts = url.pathname.split("/").filter(Boolean);
    const markerIndex = parts.findIndex((part) => ["embed", "shorts", "live"].includes(part));
    if (markerIndex >= 0) return parts[markerIndex + 1] || "";

    return "";
}

function isYouTubeId(value) {
    return /^[A-Za-z0-9_-]{11}$/.test(String(value || ""));
}

function invalid(reason) {
    return {
        valid: false,
        reason,
        kind: "invalid",
        videoId: "",
        source: "",
        embedUrl: "",
        externalUrl: "",
    };
}
