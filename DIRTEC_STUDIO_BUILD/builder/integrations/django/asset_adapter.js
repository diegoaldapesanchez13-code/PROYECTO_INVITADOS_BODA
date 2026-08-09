export class DjangoAssetAdapter {
    constructor(options = {}) {
        this.listEndpoint = options.listEndpoint;
        this.deleteEndpointTemplate =
            options.deleteEndpointTemplate;
        this.csrfToken = options.csrfToken || "";
    }

    async upload(file) {
        const form = new FormData();
        form.append("archivo", file, file.name);

        const response = await fetch(
            this.listEndpoint,
            {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": this.csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: form,
            }
        );

        const payload = await safeJson(response);

        if (!response.ok || !payload.ok) {
            throw new Error(
                payload.error
                || "No se pudo subir el archivo."
            );
        }

        return payload.asset;
    }

    async remove(assetId) {
        const databaseId =
            parseDatabaseAssetId(assetId);

        if (!databaseId) {
            return {
                ok: true,
                localOnly: true,
            };
        }

        const endpoint =
            this.deleteEndpointTemplate
                .replace("__ASSET_ID__", databaseId);

        const response = await fetch(
            endpoint,
            {
                method: "DELETE",
                credentials: "same-origin",
                headers: {
                    "X-CSRFToken": this.csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json",
                },
            }
        );

        const payload = await safeJson(response);

        if (!response.ok || !payload.ok) {
            throw new Error(
                payload.error
                || "No se pudo eliminar el recurso."
            );
        }

        return payload;
    }

    async list() {
        const response = await fetch(
            this.listEndpoint,
            {
                credentials: "same-origin",
                headers: {
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest",
                },
            }
        );

        const payload = await safeJson(response);

        if (!response.ok || !payload.ok) {
            throw new Error(
                payload.error
                || "No se pudo cargar la biblioteca."
            );
        }

        return payload.assets || [];
    }
}

export function parseDatabaseAssetId(assetId) {
    const match =
        /^db-(\d+)$/.exec(
            String(assetId || "")
        );

    return match
        ? match[1]
        : null;
}

async function safeJson(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}
