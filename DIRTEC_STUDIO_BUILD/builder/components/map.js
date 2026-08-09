const GOOGLE_MAP_HOSTS = new Set([
    "google.com",
    "www.google.com",
    "maps.google.com",
    "maps.app.goo.gl",
]);

export function normalizeMapSource(value, options = {}) {
    const raw = String(value || "").trim();
    const zoom = clamp(Number(options.zoom ?? 15), 1, 21);

    if (!raw) {
        return invalid("empty");
    }

    const iframeSource = extractIframeSource(raw);
    if (iframeSource) {
        return normalizeMapSource(iframeSource, options);
    }

    const coordinates = parseCoordinates(raw);
    if (coordinates) {
        return {
            valid: true,
            kind: "coordinates",
            source: raw,
            embedUrl: buildEmbedUrl(
                `${coordinates.latitude},${coordinates.longitude}`,
                zoom
            ),
            externalUrl: buildExternalUrl(
                `${coordinates.latitude},${coordinates.longitude}`
            ),
            coordinates,
        };
    }

    let parsed;
    try {
        parsed = new URL(raw);
    } catch {
        return {
            valid: true,
            kind: "query",
            source: raw,
            embedUrl: buildEmbedUrl(raw, zoom),
            externalUrl: buildExternalUrl(raw),
        };
    }

    if (!/^https?:$/.test(parsed.protocol)) {
        return invalid("unsupported-protocol");
    }

    const host = parsed.hostname.toLowerCase();
    if (!isGoogleMapsHost(host)) {
        return invalid("unsupported-host");
    }

    if (host === "maps.app.goo.gl") {
        return {
            valid: true,
            kind: "short-link",
            source: raw,
            embedUrl: "",
            externalUrl: raw,
            requiresResolution: true,
        };
    }

    if (parsed.pathname.includes("/maps/embed")) {
        return {
            valid: true,
            kind: "embed-url",
            source: raw,
            embedUrl: raw,
            externalUrl: raw,
        };
    }

    const query = extractMapQuery(parsed);
    if (!query) {
        return invalid("missing-location");
    }

    return {
        valid: true,
        kind: "google-maps-url",
        source: raw,
        embedUrl: buildEmbedUrl(query, zoom),
        externalUrl: raw,
    };
}

export function buildEmbedUrl(query, zoom = 15) {
    const url = new URL("https://www.google.com/maps");
    url.searchParams.set("q", String(query || "").trim());
    url.searchParams.set("z", String(clamp(Number(zoom || 15), 1, 21)));
    url.searchParams.set("output", "embed");
    return url.toString();
}

export function buildExternalUrl(query) {
    const url = new URL("https://www.google.com/maps/search/");
    url.searchParams.set("api", "1");
    url.searchParams.set("query", String(query || "").trim());
    return url.toString();
}

export function extractIframeSource(value) {
    const match = String(value || "").match(
        /<iframe[^>]+src=["']([^"']+)["']/i
    );
    return match?.[1] || "";
}

function extractMapQuery(url) {
    const direct =
        url.searchParams.get("query")
        || url.searchParams.get("q")
        || url.searchParams.get("destination");

    if (direct) return direct;

    const atMatch = url.pathname.match(
        /@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/
    );
    if (atMatch) return `${atMatch[1]},${atMatch[2]}`;

    const placeMatch = url.pathname.match(/\/maps\/place\/([^/]+)/i);
    if (placeMatch) {
        return decodeURIComponent(placeMatch[1].replace(/\+/g, " "));
    }

    return "";
}

function parseCoordinates(value) {
    const match = String(value || "").match(
        /^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$/
    );

    if (!match) return null;

    const latitude = Number(match[1]);
    const longitude = Number(match[2]);

    if (
        !Number.isFinite(latitude)
        || !Number.isFinite(longitude)
        || latitude < -90
        || latitude > 90
        || longitude < -180
        || longitude > 180
    ) {
        return null;
    }

    return { latitude, longitude };
}

function isGoogleMapsHost(host) {
    return GOOGLE_MAP_HOSTS.has(host)
        || host.endsWith(".google.com");
}

function invalid(reason) {
    return {
        valid: false,
        reason,
        kind: "invalid",
        source: "",
        embedUrl: "",
        externalUrl: "",
    };
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
