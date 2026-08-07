/**
 * Crea adaptadores de Assets para un backend Django.
 * El Engine solo conoce funciones upload/delete; no conoce URLs ni CSRF.
 */
export function createDjangoAssetAdapters(options = {}) {
    const { uploadUrl, deleteUrl = null, csrfToken = "", fetchImpl = globalThis.fetch } = options;
    if (!uploadUrl) throw new TypeError("uploadUrl es obligatorio.");
    if (typeof fetchImpl !== "function") throw new TypeError("fetchImpl debe ser una función.");

    return {
        uploader: async (file, metadata = {}) => {
            const formData = new FormData();
            formData.append("archivo", file);
            for (const [key, value] of Object.entries(metadata)) {
                if (value !== undefined && value !== null && typeof value !== "object") formData.append(key, String(value));
            }
            const response = await fetchImpl(uploadUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                body: formData,
            });
            const payload = await parseJson(response);
            if (!response.ok || payload.ok === false) throw new Error(payload.error || "No fue posible subir el archivo.");
            const asset = payload.asset || payload;
            return {
                id: String(asset.id),
                backendId: asset.id,
                name: asset.name || asset.title || file.name,
                url: asset.url,
                previewUrl: asset.previewUrl || asset.url,
                mimeType: asset.mimeType || file.type,
                size: asset.size || file.size,
                type: asset.type,
                source: "UPLOAD",
                storageKey: asset.storageKey || asset.path || null,
                metadata: asset.metadata || {},
            };
        },
        deleter: deleteUrl ? async (asset) => {
            const formData = new FormData();
            formData.append("asset_id", String(asset.backendId ?? asset.id));
            const response = await fetchImpl(deleteUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
                body: formData,
            });
            const payload = await parseJson(response);
            if (!response.ok || payload.ok === false) throw new Error(payload.error || "No fue posible eliminar el archivo.");
            return payload;
        } : null,
    };
}

async function parseJson(response) {
    try { return await response.json(); } catch { return {}; }
}
