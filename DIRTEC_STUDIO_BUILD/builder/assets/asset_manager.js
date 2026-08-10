import {
    createId,
} from "../core/index.js";

export const ASSET_TYPES = Object.freeze({
    IMAGE: "IMAGE",
    BACKGROUND: "BACKGROUND",
    DECORATION: "DECORATION",
    TEXTURE: "TEXTURE",
    ICON: "ICON",
    VIDEO: "VIDEO",
    AUDIO: "AUDIO",
});

export const ASSET_SOURCES = Object.freeze({
    BUILTIN: "BUILTIN",
    UPLOAD: "UPLOAD",
    REMOTE: "REMOTE",
});

export class AssetManager {
    #assets = new Map();
    #listeners = new Set();
    #recentIds = [];
    #storage = null;

    constructor(options = {}) {
        const {
            initialAssets = [],
            storage = null,
        } = Array.isArray(options)
            ? {
                initialAssets: options,
                storage: null,
            }
            : options;

        this.#storage = storage;

        /*
         * Los assets integrados se registran sin persistir.
         * Si se guardaran aquí, sobrescribirían localStorage
         * antes de restaurar los uploads del usuario.
         */
        this.registerMany(initialAssets, {
            silent: true,
            persist: false,
        });

        this.restore();
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError(
                "listener debe ser una función."
            );
        }

        this.#listeners.add(listener);

        return () => {
            this.#listeners.delete(listener);
        };
    }

    register(rawAsset, options = {}) {
        const {
            silent = false,
            persist = true,
        } = options;

        const asset = normalizeAsset(rawAsset);
        this.#assets.set(asset.id, asset);

        if (persist) {
            this.persist();
        }

        if (!silent) {
            this.#emit(
                "asset:register",
                asset
            );
        }

        return clone(asset);
    }

    registerMany(
        assets = [],
        options = {}
    ) {
        for (const asset of assets) {
            this.register(asset, {
                ...options,
                persist: false,
            });
        }

        if (options.persist !== false) {
            this.persist();
        }

        return this.list();
    }

    upsert(rawAsset) {
        return this.register(rawAsset);
    }

    remove(assetId) {
        const asset =
            this.#assets.get(
                String(assetId)
            );

        if (!asset) {
            return false;
        }

        if (
            asset.source
            === ASSET_SOURCES.BUILTIN
        ) {
            throw new Error(
                "Los recursos integrados no se eliminan."
            );
        }

        this.#assets.delete(asset.id);

        this.#recentIds =
            this.#recentIds.filter(
                (id) => id !== asset.id
            );

        this.persist();

        this.#emit(
            "asset:remove",
            asset
        );

        return true;
    }

    get(assetId) {
        const asset =
            this.#assets.get(
                String(assetId)
            );

        return asset
            ? clone(asset)
            : null;
    }

    resolve(assetId) {
        return this.get(assetId)?.url || "";
    }

    use(assetId) {
        const asset =
            this.#assets.get(
                String(assetId)
            );

        if (!asset) {
            return null;
        }

        asset.useCount += 1;
        asset.lastUsedAt =
            new Date().toISOString();
        asset.updatedAt =
            asset.lastUsedAt;

        this.#recentIds = [
            asset.id,
            ...this.#recentIds.filter(
                (id) => id !== asset.id
            ),
        ].slice(0, 30);

        this.persist();

        this.#emit(
            "asset:use",
            asset
        );

        return clone(asset);
    }

    toggleFavorite(assetId) {
        const asset =
            this.#assets.get(
                String(assetId)
            );

        if (!asset) {
            throw new Error(
                `Asset no encontrado: ${assetId}`
            );
        }

        asset.favorite = !asset.favorite;
        asset.updatedAt =
            new Date().toISOString();

        this.persist();

        this.#emit(
            "asset:favorite",
            asset
        );

        return clone(asset);
    }

    list(filters = {}) {
        const {
            type = null,
            category = null,
            collection = null,
            source = null,
            favorite = null,
            recent = false,
            query = "",
            limit = null,
        } = filters;

        const normalizedQuery =
            String(query)
                .trim()
                .toLowerCase();

        let assets =
            [...this.#assets.values()]
                .filter((asset) => {
                    if (
                        type
                        && asset.type !== type
                    ) {
                        return false;
                    }

                    if (
                        category
                        && asset.category
                            !== category
                    ) {
                        return false;
                    }

                    if (
                        collection
                        && asset.collection
                            !== collection
                    ) {
                        return false;
                    }

                    if (
                        source
                        && asset.source
                            !== source
                    ) {
                        return false;
                    }

                    if (
                        favorite !== null
                        && asset.favorite
                            !== favorite
                    ) {
                        return false;
                    }

                    if (!normalizedQuery) {
                        return true;
                    }

                    const haystack = [
                        asset.name,
                        asset.category,
                        asset.collection,
                        asset.type,
                        ...asset.tags,
                    ]
                        .join(" ")
                        .toLowerCase();

                    return haystack.includes(
                        normalizedQuery
                    );
                });

        if (recent) {
            const order =
                new Map(
                    this.#recentIds.map(
                        (id, index) => [
                            id,
                            index,
                        ]
                    )
                );

            assets = assets
                .filter(
                    (asset) =>
                        order.has(asset.id)
                )
                .sort(
                    (a, b) =>
                        order.get(a.id)
                        - order.get(b.id)
                );
        } else {
            assets.sort(
                (a, b) =>
                    a.order - b.order
                    || b.useCount - a.useCount
                    || a.name.localeCompare(
                        b.name
                    )
            );
        }

        if (
            Number.isInteger(limit)
            && limit >= 0
        ) {
            assets = assets.slice(
                0,
                limit
            );
        }

        return assets.map(clone);
    }

    categories() {
        return [
            ...new Set(
                [...this.#assets.values()]
                    .map(
                        (asset) =>
                            asset.category
                    )
                    .filter(Boolean)
            ),
        ].sort(
            (a, b) =>
                a.localeCompare(b)
        );
    }

    collections() {
        return [
            ...new Set(
                [...this.#assets.values()]
                    .map(
                        (asset) =>
                            asset.collection
                    )
                    .filter(Boolean)
            ),
        ].sort(
            (a, b) =>
                a.localeCompare(b)
        );
    }

    serializeUploads() {
        return [...this.#assets.values()]
            .filter(
                (asset) =>
                    asset.source
                    !== ASSET_SOURCES.BUILTIN
            )
            .map(clone);
    }

    persist() {
        if (!this.#storage) {
            return false;
        }

        this.#storage.save({
            uploads:
                this.serializeUploads(),
            recentIds: [
                ...this.#recentIds,
            ],
        });

        return true;
    }

    restore() {
        if (!this.#storage) {
            return false;
        }

        const saved =
            this.#storage.load();

        if (!saved) {
            return false;
        }

        this.registerMany(
            saved.uploads || [],
            {
                silent: true,
                persist: false,
            }
        );

        this.#recentIds =
            Array.isArray(
                saved.recentIds
            )
                ? saved.recentIds
                    .map(String)
                    .filter(
                        (id) =>
                            this.#assets.has(id)
                    )
                : [];

        return true;
    }

    #emit(type, asset) {
        const event = {
            type,
            asset: clone(asset),
        };

        for (
            const listener
            of this.#listeners
        ) {
            listener(event);
        }
    }
}

export function normalizeAsset(
    rawAsset = {}
) {
    const now =
        new Date().toISOString();

    const type =
        Object.values(ASSET_TYPES)
            .includes(rawAsset.type)
            ? rawAsset.type
            : ASSET_TYPES.IMAGE;

    const source =
        Object.values(ASSET_SOURCES)
            .includes(rawAsset.source)
            ? rawAsset.source
            : ASSET_SOURCES.BUILTIN;

    return {
        id:
            String(
                rawAsset.id
                || createId("asset")
            ),
        type,
        source,
        name:
            String(
                rawAsset.name
                || "Recurso"
            ),
        category:
            String(
                rawAsset.category
                || "General"
            ),
        collection:
            String(
                rawAsset.collection
                || "General"
            ),
        url:
            String(rawAsset.url || ""),
        previewUrl:
            String(
                rawAsset.previewUrl
                || rawAsset.url
                || ""
            ),
        mimeType:
            String(
                rawAsset.mimeType
                || guessMimeType(
                    rawAsset.url,
                    type
                )
            ),
        tags:
            Array.isArray(rawAsset.tags)
                ? [
                    ...new Set(
                        rawAsset.tags
                            .map(String)
                    ),
                ]
                : [],
        favorite:
            Boolean(
                rawAsset.favorite
            ),
        order:
            finite(
                rawAsset.order,
                0
            ),
        useCount:
            finite(
                rawAsset.useCount,
                0
            ),
        lastUsedAt:
            rawAsset.lastUsedAt
            || null,
        metadata: {
            transparent:
                Boolean(
                    rawAsset.metadata
                        ?.transparent
                ),
            supportsAlpha:
                Boolean(
                    rawAsset.metadata
                        ?.supportsAlpha
                ),
            animated:
                Boolean(
                    rawAsset.metadata
                        ?.animated
                ),
            mediaKind:
                String(
                    rawAsset.metadata
                        ?.mediaKind
                    || (
                        type === ASSET_TYPES.VIDEO
                            ? "VIDEO"
                            : type === ASSET_TYPES.AUDIO
                                ? "AUDIO"
                                : "IMAGE"
                    )
                ),
            aspectRatio:
                finite(
                    rawAsset.metadata
                        ?.aspectRatio,
                    1
                ),
            width:
                finite(
                    rawAsset.metadata
                        ?.width,
                    0
                ),
            height:
                finite(
                    rawAsset.metadata
                        ?.height,
                    0
                ),
            size:
                finite(
                    rawAsset.metadata
                        ?.size,
                    0
                ),
            ...clone(
                rawAsset.metadata || {}
            ),
        },
        createdAt:
            rawAsset.createdAt || now,
        updatedAt:
            rawAsset.updatedAt || now,
    };
}

function guessMimeType(url = "", type = ASSET_TYPES.IMAGE) {
    const value =
        String(url).toLowerCase();

    if (
        value.startsWith(
            "data:image/svg+xml"
        )
        || value.endsWith(".svg")
    ) {
        return "image/svg+xml";
    }

    if (
        value.startsWith(
            "data:image/png"
        )
        || value.endsWith(".png")
    ) {
        return "image/png";
    }

    if (
        value.startsWith(
            "data:image/webp"
        )
        || value.endsWith(".webp")
    ) {
        return "image/webp";
    }

    if (
        value.startsWith(
            "data:image/gif"
        )
        || value.endsWith(".gif")
    ) {
        return "image/gif";
    }

    if (
        value.startsWith(
            "data:video/"
        )
        || value.endsWith(".mp4")
        || (
            type === ASSET_TYPES.VIDEO
            && value.endsWith(".ogg")
        )
    ) {
        return value.endsWith(".ogg")
            ? "video/ogg"
            : "video/mp4";
    }

    if (
        value.startsWith(
            "data:audio/"
        )
        || value.endsWith(".mp3")
        || value.endsWith(".m4a")
        || value.endsWith(".wav")
        || (
            type === ASSET_TYPES.AUDIO
            && value.endsWith(".ogg")
        )
    ) {
        if (value.endsWith(".wav")) {
            return "audio/wav";
        }
        if (value.endsWith(".m4a")) {
            return "audio/mp4";
        }
        if (value.endsWith(".ogg")) {
            return "audio/ogg";
        }
        return "audio/mpeg";
    }

    return "image/jpeg";
}

function finite(value, fallback) {
    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : fallback;
}

function clone(value) {
    if (
        typeof structuredClone
        === "function"
    ) {
        return structuredClone(value);
    }

    return JSON.parse(
        JSON.stringify(value)
    );
}
