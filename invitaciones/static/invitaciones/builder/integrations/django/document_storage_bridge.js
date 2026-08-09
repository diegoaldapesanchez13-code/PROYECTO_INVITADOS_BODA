const EVENT_NAME = "dirtec:builder-persistence";

export class DjangoDocumentStorageBridge {
    constructor(options = {}) {
        this.document = options.initialDocument || null;
        this.revision = Number(options.revision || 0);
        this.endpoint = options.endpoint;
        this.publishEndpoint = options.publishEndpoint;
        this.csrfToken = options.csrfToken || "";
        this.pending = null;
        this.saving = false;
        this.flushPromise = null;
    }

    getItem() {
        return this.document
            ? JSON.stringify(this.document)
            : null;
    }

    setItem(_key, rawValue) {
        const document = JSON.parse(rawValue);
        this.document = document;
        this.pending = { document, reset: false };
        this.#schedule();
    }

    removeItem() {
        this.document = null;
        this.pending = { document: null, reset: true };
        this.#schedule();
    }

    async flush() {
        this.#schedule();
        if (this.flushPromise) {
            await this.flushPromise;
        }
    }

    async publish() {
        await this.flush();
        this.#emit("publishing", "Publicando…");

        const response = await fetch(this.publishEndpoint, {
            method: "POST",
            credentials: "same-origin",
            keepalive: true,
            headers: this.#headers(),
            body: JSON.stringify({
                baseRevision: this.revision,
            }),
        });

        const payload = await safeJson(response);
        if (!response.ok || !payload.ok) {
            this.#emit("error", payload.error || "No fue posible publicar.");
            throw new Error(payload.error || "No fue posible publicar.");
        }

        this.#emit("published", "Publicado", payload);
        return payload;
    }

    #schedule() {
        if (this.saving || !this.pending) {
            return;
        }

        this.flushPromise = this.#drain()
            .finally(() => {
                this.flushPromise = null;
            });
    }

    async #drain() {
        this.saving = true;

        try {
            while (this.pending) {
                const next = this.pending;
                this.pending = null;
                await this.#save(next);
            }
        } finally {
            this.saving = false;
            if (this.pending) {
                this.#schedule();
            }
        }
    }

    async #save(next) {
        this.#emit("saving", "Guardando…");

        const response = await fetch(this.endpoint, {
            method: "POST",
            credentials: "same-origin",
            keepalive: true,
            headers: this.#headers(),
            body: JSON.stringify({
                document: next.document,
                reset: next.reset,
                baseRevision: this.revision,
            }),
        });

        const payload = await safeJson(response);

        if (!response.ok || !payload.ok) {
            this.#emit("error", payload.error || "Error al guardar.");
            throw new Error(payload.error || "Error al guardar.");
        }

        this.revision = Number(payload.revision || this.revision);
        this.#emit("saved", "Guardado", payload);
    }

    #headers() {
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-CSRFToken": this.csrfToken,
            "X-Requested-With": "XMLHttpRequest",
        };
    }

    #emit(state, message, payload = {}) {
        globalThis.dispatchEvent(
            new CustomEvent(EVENT_NAME, {
                detail: {
                    state,
                    message,
                    revision: this.revision,
                    ...payload,
                },
            }),
        );
    }
}

export function persistenceEventName() {
    return EVENT_NAME;
}

async function safeJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}
