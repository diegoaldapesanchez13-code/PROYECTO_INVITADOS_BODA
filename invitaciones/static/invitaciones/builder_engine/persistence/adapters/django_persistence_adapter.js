/**
 * Adaptador Django sin rutas embebidas.
 * Las URLs se inyectan desde el template/bootstrap del host.
 */
export function createDjangoPersistenceAdapter(options = {}) {
    const fetchImpl = options.fetchImpl || globalThis.fetch;
    if (typeof fetchImpl !== "function") {
        throw new TypeError("DjangoPersistenceAdapter requiere fetch().");
    }

    const endpoints = normalizeEndpoints(options.endpoints);
    const getCsrfToken = options.getCsrfToken || (() => options.csrfToken || "");

    return Object.freeze({
        async load(context = {}) {
            const response = await fetchImpl(
                context.url || endpoints.load,
                requestOptions("GET", null, getCsrfToken()),
            );
            return parseJsonResponse(response);
        },

        async save({ document, reason, context = {} }) {
            const response = await fetchImpl(
                context.url || endpoints.save,
                requestOptions("POST", { document, reason }, getCsrfToken()),
            );
            return parseJsonResponse(response);
        },

        async publish({ document, context = {} }) {
            const response = await fetchImpl(
                context.url || endpoints.publish,
                requestOptions("POST", { document }, getCsrfToken()),
            );
            return parseJsonResponse(response);
        },
    });
}

function normalizeEndpoints(value = {}) {
    const endpoints = {
        load: String(value.load || ""),
        save: String(value.save || ""),
        publish: String(value.publish || ""),
    };
    for (const [name, url] of Object.entries(endpoints)) {
        if (!url) throw new TypeError(`Falta endpoint Django: ${name}.`);
    }
    return Object.freeze(endpoints);
}

function requestOptions(method, body, csrfToken) {
    const headers = { Accept: "application/json" };
    if (body !== null) headers["Content-Type"] = "application/json";
    if (csrfToken) headers["X-CSRFToken"] = csrfToken;
    return {
        method,
        credentials: "same-origin",
        headers,
        body: body === null ? undefined : JSON.stringify(body),
    };
}

async function parseJsonResponse(response) {
    let payload = {};
    try {
        payload = await response.json();
    } catch {
        payload = {};
    }
    if (!response.ok) {
        const message = payload.error || payload.detail || `HTTP ${response.status}`;
        throw new Error(message);
    }
    return payload;
}
