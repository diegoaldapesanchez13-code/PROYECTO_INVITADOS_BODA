const SAFE_WEB_PROTOCOLS = new Set([
    "http:",
    "https:",
]);

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

function invalid(code, message) {
    return {
        valid: false,
        value: "",
        code,
        message,
    };
}
