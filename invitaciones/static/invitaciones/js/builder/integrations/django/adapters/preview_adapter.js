export class DjangoPreviewAdapter {
    constructor({ previewUrl = "" } = {}) {
        this.previewUrl = previewUrl;
    }

    buildUrl({ uuid = "", draft = true } = {}) {
        if (!this.previewUrl) return "";
        const url = new URL(this.previewUrl, globalThis.location?.origin || "http://localhost");
        if (uuid) url.searchParams.set("uuid", uuid);
        if (draft) url.searchParams.set("preview", "1");
        return url.toString();
    }
}
