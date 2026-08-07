export class AssetManagerService {
    #endpoint;
    #fetch;
    #assets = [];
    #listeners = new Set();
    #loading = false;
    #error = null;

    constructor(options = {}) {
        if (!options.endpoint) {
            throw new TypeError("AssetManager requiere endpoint.");
        }

        this.#endpoint = String(options.endpoint);

        if (options.fetchImpl) {
            this.#fetch = options.fetchImpl;
        } else if (typeof globalThis.fetch === "function") {
            // fetch depende del contexto Window en algunos navegadores.
            this.#fetch = globalThis.fetch.bind(globalThis);
        } else {
            throw new TypeError("AssetManager requiere fetch().");
        }
    }

    get assets() {
        return clone(this.#assets);
    }

    get loading() {
        return this.#loading;
    }

    get error() {
        return this.#error;
    }

    async load(filters = {}) {
        this.#loading = true;
        this.#error = null;
        this.#emit();

        try {
            const origin = globalThis.location?.origin || "http://localhost";
            const url = new URL(this.#endpoint, origin);

            if (filters.type) {
                url.searchParams.set("type", filters.type);
            }

            if (filters.query) {
                url.searchParams.set("q", filters.query);
            }

            const requestUrl = (
                url.origin === origin
                    ? `${url.pathname}${url.search}`
                    : url.toString()
            );

            const response = await this.#fetch(requestUrl, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            });

            let payload;
            try {
                payload = await response.json();
            } catch {
                throw new Error(
                    `La biblioteca respondió con un formato inválido (HTTP ${response.status}).`
                );
            }

            if (!response.ok || !payload.ok) {
                throw new Error(
                    payload.error
                    || payload.detail
                    || `No fue posible cargar los archivos (HTTP ${response.status}).`
                );
            }

            this.#assets = normalizeAssets(payload.assets);
            return this.assets;
        } catch (error) {
            this.#error = friendlyError(error);
            throw error;
        } finally {
            this.#loading = false;
            this.#emit();
        }
    }

    find(assetId) {
        const asset = this.#assets.find(
            (item) => item.id === String(assetId)
        );
        return asset ? clone(asset) : null;
    }

    filtered(options = {}) {
        const type = String(options.type || "ALL").toUpperCase();
        const query = String(options.query || "").trim().toLowerCase();

        return this.#assets
            .filter((asset) => {
                const matchesType = (
                    type === "ALL"
                    || asset.type === type
                    || (type === "IMAGE" && asset.type === "GIF")
                );

                const matchesQuery = (
                    !query
                    || asset.name.toLowerCase().includes(query)
                    || asset.category.toLowerCase().includes(query)
                    || String(asset.metadata?.filename || "")
                        .toLowerCase()
                        .includes(query)
                );

                return matchesType && matchesQuery;
            })
            .map(clone);
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError("listener debe ser función.");
        }

        this.#listeners.add(listener);
        listener(this.state());

        return () => {
            this.#listeners.delete(listener);
        };
    }

    state() {
        return Object.freeze({
            assets: this.assets,
            loading: this.#loading,
            error: this.#error,
        });
    }

    #emit() {
        const state = this.state();

        for (const listener of this.#listeners) {
            listener(state);
        }
    }
}

function normalizeAssets(values = []) {
    return values
        .filter((asset) => asset && asset.id && asset.url)
        .map((asset) => ({
            id: String(asset.id),
            backendId: Number(asset.backendId || asset.id),
            eventId: asset.eventId,
            sectionId: asset.sectionId,
            type: String(asset.type || "IMAGE").toUpperCase(),
            category: String(asset.category || "DECORACION"),
            source: String(asset.source || "UPLOAD"),
            name: String(asset.name || "Asset"),
            url: String(asset.url),
            mimeType: String(asset.mimeType || ""),
            size: Number(asset.size || 0),
            visible: asset.visible !== false,
            order: Number(asset.order || 0),
            createdAt: asset.createdAt || null,
            metadata: asset.metadata || {},
        }));
}

function friendlyError(error) {
    const message = error instanceof Error
        ? error.message
        : String(error || "Error desconocido");

    if (message.includes("Illegal invocation")) {
        return "El navegador no pudo iniciar la solicitud de archivos. Recarga la página después de aplicar el hotfix.";
    }

    if (message.includes("Failed to fetch")) {
        return "No fue posible conectar con la biblioteca de archivos.";
    }

    return message;
}

function clone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
