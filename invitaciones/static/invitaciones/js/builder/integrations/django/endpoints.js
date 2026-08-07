export class DjangoEndpoints {
    #urls;
    #csrfToken;
    #fetch;

    constructor({ urls = {}, csrfToken = "", fetchImpl = globalThis.fetch } = {}) {
        this.#urls = { ...urls };
        this.#csrfToken = csrfToken;
        this.#fetch = fetchImpl;
    }

    get urls() {
        return { ...this.#urls };
    }

    async saveDocument(document) {
        return this.#postJson("save", { document });
    }

    async publishDocument(document) {
        return this.#postJson("publish", { document });
    }

    async uploadAsset(file, fields = {}) {
        const url = this.#requireUrl("uploadAsset");
        const form = new FormData();
        form.append("archivo", file);
        for (const [key, value] of Object.entries(fields)) {
            if (value !== undefined && value !== null) {
                form.append(key, String(value));
            }
        }
        return this.#request(url, {
            method: "POST",
            body: form,
            headers: this.#csrfToken ? { "X-CSRFToken": this.#csrfToken } : {},
        });
    }

    async #postJson(key, payload) {
        const url = this.#requireUrl(key);
        return this.#request(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(this.#csrfToken ? { "X-CSRFToken": this.#csrfToken } : {}),
            },
            body: JSON.stringify(payload),
        });
    }

    async #request(url, options) {
        if (typeof this.#fetch !== "function") {
            throw new Error("No hay implementación fetch disponible.");
        }
        const response = await this.#fetch(url, options);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || data.detail || `Error HTTP ${response.status}`);
        }
        return data;
    }

    #requireUrl(key) {
        const url = this.#urls[key];
        if (!url) {
            throw new Error(`Endpoint Django no configurado: ${key}`);
        }
        return url;
    }
}
