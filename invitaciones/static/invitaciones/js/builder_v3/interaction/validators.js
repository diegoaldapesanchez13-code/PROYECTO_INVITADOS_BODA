const SAFE_WEB_PROTOCOLS = new Set([
    "http:",
    "https:",
]);

const GOOGLE_MAP_HOSTS = new Set([
    "maps.app.goo.gl",
    "goo.gl",
    "maps.google.com",
    "www.google.com",
    "google.com",
]);

const COORDINATE_PATTERN = /^\s*(-?\d{1,3}(?:\.\d+)?)\s*[,;]\s*(-?\d{1,3}(?:\.\d+)?)\s*$/;

export function validateWebUrl(value) {
    const input = String(value || "").trim();

    if (!input) {
        return invalid(
            "url-required",
            "Ingresa una URL."
        );
    }

    let parsed;

    try {
        parsed = new URL(input);
    } catch {
        return invalid(
            "url-invalid",
            "La URL no tiene un formato válido."
        );
    }

    if (!SAFE_WEB_PROTOCOLS.has(parsed.protocol)) {
        return invalid(
            "url-protocol-not-allowed",
            "Solo se permiten URLs HTTP o HTTPS."
        );
    }

    return {
        valid: true,
        value: input,
        code: null,
        message: "",
    };
}

export function validateGoogleMapsValue(value) {
    const input = String(value || "").trim();

    if (!input) {
        return invalid(
            "maps-value-required",
            "Ingresa un enlace de Google Maps o coordenadas."
        );
    }

    const coordinates = parseCoordinates(input);

    if (coordinates) {
        const { latitude, longitude } = coordinates;

        if (!validLatitude(latitude)) {
            return invalid(
                "maps-latitude-invalid",
                "La latitud debe estar entre -90 y 90."
            );
        }

        if (!validLongitude(longitude)) {
            return invalid(
                "maps-longitude-invalid",
                "La longitud debe estar entre -180 y 180."
            );
        }

        return {
            valid: true,
            value: googleMapsSearchUrl(
                latitude,
                longitude
            ),
            source: "coordinates",
            coordinates: {
                latitude,
                longitude,
            },
            code: null,
            message: "",
        };
    }

    const urlValidation = validateWebUrl(input);

    if (!urlValidation.valid) {
        return invalid(
            "maps-url-invalid",
            "Ingresa un enlace válido de Google Maps o coordenadas."
        );
    }

    const parsed = new URL(urlValidation.value);
    const host = parsed.hostname.toLowerCase();

    if (!isGoogleMapsHost(host)) {
        return invalid(
            "maps-host-not-allowed",
            "El enlace debe pertenecer a Google Maps."
        );
    }

    if (!isGoogleMapsPath(parsed)) {
        return invalid(
            "maps-path-invalid",
            "El enlace no corresponde a una ubicación de Google Maps."
        );
    }

    return {
        valid: true,
        value: parsed.href,
        source: "url",
        coordinates: null,
        code: null,
        message: "",
    };
}

export function googleMapsSearchUrl(
    latitude,
    longitude
) {
    const query = encodeURIComponent(
        `${Number(latitude)},${Number(longitude)}`
    );

    return `https://www.google.com/maps/search/?api=1&query=${query}`;
}

function parseCoordinates(input) {
    const match = String(input).match(
        COORDINATE_PATTERN
    );

    if (!match) {
        return null;
    }

    const latitude = Number(match[1]);
    const longitude = Number(match[2]);

    if (
        !Number.isFinite(latitude)
        || !Number.isFinite(longitude)
    ) {
        return null;
    }

    return {
        latitude,
        longitude,
    };
}

function validLatitude(value) {
    return value >= -90 && value <= 90;
}

function validLongitude(value) {
    return value >= -180 && value <= 180;
}

function isGoogleMapsHost(host) {
    if (GOOGLE_MAP_HOSTS.has(host)) {
        return true;
    }

    return (
        host.endsWith(".google.com")
        || host.endsWith(".google.com.mx")
        || host.endsWith(".googleusercontent.com")
    );
}

function isGoogleMapsPath(parsed) {
    const host = parsed.hostname.toLowerCase();
    const path = parsed.pathname.toLowerCase();

    if (
        host === "maps.app.goo.gl"
        || host === "goo.gl"
        || host === "maps.google.com"
    ) {
        return true;
    }

    return (
        path === "/maps"
        || path.startsWith("/maps/")
        || path.startsWith("/maps/search")
        || path.startsWith("/maps/place")
        || parsed.searchParams.has("q")
        || parsed.searchParams.has("query")
        || parsed.searchParams.get("api") === "1"
    );
}

function invalid(code, message) {
    return {
        valid: false,
        value: "",
        source: null,
        coordinates: null,
        code,
        message,
    };
}
