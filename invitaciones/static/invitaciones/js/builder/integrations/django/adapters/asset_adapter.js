export class DjangoAssetAdapter {
    fromBackend(asset = {}) {
        return {
            id: String(asset.id ?? asset.assetId ?? ""),
            name: String(asset.name || asset.titulo || asset.filename || "Asset"),
            type: String(asset.type || asset.tipo || inferType(asset.mimeType || asset.mime || "")),
            url: String(asset.url || asset.archivo_url || asset.fileUrl || ""),
            mimeType: String(asset.mimeType || asset.mime || ""),
            size: Number(asset.size || 0),
            metadata: asset.metadata && typeof asset.metadata === "object" ? { ...asset.metadata } : {},
        };
    }

    listFromBackend(assets = []) {
        return Array.isArray(assets) ? assets.map((asset) => this.fromBackend(asset)) : [];
    }
}

function inferType(mime) {
    if (String(mime).startsWith("video/")) return "video";
    if (String(mime).startsWith("audio/")) return "audio";
    return "image";
}
