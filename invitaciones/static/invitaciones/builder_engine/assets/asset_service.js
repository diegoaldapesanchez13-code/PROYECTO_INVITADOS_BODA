import { normalizeAsset, sanitizeAssetForDocument, validateAsset } from "./asset_schema.js";

export class AssetService {
    #app;
    #uploader;
    #deleter;

    constructor({ app, uploader = null, deleter = null } = {}) {
        if (!app || typeof app.getDocument !== "function") throw new TypeError("AssetService requiere BuilderApp.");
        this.#app = app;
        this.#uploader = uploader;
        this.#deleter = deleter;
    }

    list(filters = {}) {
        const assets = this.#assets();
        const query = String(filters.query || "").trim().toLowerCase();
        return assets.filter((asset) => {
            if (filters.type && asset.type !== filters.type) return false;
            if (filters.source && asset.source !== filters.source) return false;
            if (filters.category && asset.category !== filters.category) return false;
            if (query) {
                const haystack = [asset.name, asset.category, ...(asset.tags || [])].join(" ").toLowerCase();
                if (!haystack.includes(query)) return false;
            }
            return true;
        }).map(clone);
    }

    get(assetId) {
        const asset = this.#assets().find((item) => String(item.id) === String(assetId));
        return asset ? clone(asset) : null;
    }

    resolve(assetId) {
        return this.get(assetId)?.url || "";
    }

    add(rawAsset) {
        const asset = sanitizeAssetForDocument(rawAsset);
        const validation = validateAsset(asset);
        if (!validation.valid) throw new Error(validation.errors.join(" "));
        this.#app.updateDocument((document) => {
            const assets = Array.isArray(document.assets) ? [...document.assets] : [];
            if (assets.some((item) => String(item.id) === asset.id)) throw new Error(`El asset "${asset.id}" ya existe.`);
            document.assets = [...assets, asset];
        }, { source: "assets:add", assetId: asset.id });
        return clone(asset);
    }

    update(assetId, patch = {}) {
        let updated = null;
        this.#app.updateDocument((document) => {
            const index = document.assets.findIndex((item) => String(item.id) === String(assetId));
            if (index < 0) throw new Error(`Asset no encontrado: ${assetId}`);
            updated = sanitizeAssetForDocument({ ...document.assets[index], ...patch, id: document.assets[index].id, updatedAt: new Date().toISOString() });
            document.assets = document.assets.map((item, itemIndex) => itemIndex === index ? updated : item);
        }, { source: "assets:update", assetId: String(assetId) });
        return clone(updated);
    }

    async upload(file, metadata = {}) {
        if (!file) throw new TypeError("Selecciona un archivo para subir.");
        if (typeof this.#uploader !== "function") throw new Error("No hay un adaptador de subida configurado.");
        const response = await this.#uploader(file, metadata);
        return this.add(normalizeAsset({ ...response, ...metadata, size: response?.size ?? file.size, mimeType: response?.mimeType || file.type, originalName: file.name }));
    }

    async remove(assetId, options = {}) {
        const asset = this.get(assetId);
        if (!asset) return false;
        if (this.isReferenced(assetId) && options.force !== true) {
            throw new Error("El asset está siendo utilizado por al menos una capa.");
        }
        if (options.deleteRemote !== false && typeof this.#deleter === "function") await this.#deleter(asset);
        this.#app.updateDocument((document) => {
            document.assets = document.assets.filter((item) => String(item.id) !== String(assetId));
        }, { source: "assets:remove", assetId: String(assetId) });
        return true;
    }

    references(assetId) {
        const results = [];
        const visit = (value, path = "") => {
            if (Array.isArray(value)) return value.forEach((item, index) => visit(item, `${path}[${index}]`));
            if (!value || typeof value !== "object") return;
            for (const [key, child] of Object.entries(value)) {
                const nextPath = path ? `${path}.${key}` : key;
                if ((key === "assetId" || key.endsWith("AssetId")) && String(child) === String(assetId)) results.push(nextPath);
                else visit(child, nextPath);
            }
        };
        visit(this.#app.getDocument().canvases || [], "canvases");
        visit(this.#app.getDocument().globals || {}, "globals");
        return results;
    }

    isReferenced(assetId) {
        return this.references(assetId).length > 0;
    }

    destroy() {}

    #assets() {
        const assets = this.#app.getDocument().assets;
        return Array.isArray(assets) ? assets : [];
    }
}

function clone(value) {
    return typeof structuredClone === "function" ? structuredClone(value) : JSON.parse(JSON.stringify(value));
}
