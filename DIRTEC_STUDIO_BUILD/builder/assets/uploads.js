import {
    ASSET_SOURCES,
    ASSET_TYPES,
} from "./asset_manager.js";

const ACCEPTED_MIME_TYPES =
    new Set([
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/svg+xml",
        "image/gif",
        "video/mp4",
        "video/webm",
        "video/ogg",
        "video/quicktime",
        "video/x-m4v",
    ]);

export class AssetUploadService {
    constructor(options = {}) {
        const {
            manager,
            maxBytes =
                12 * 1024 * 1024,
            uploader = null,
            deleter = null,
        } = options;

        if (!manager) {
            throw new Error(
                "AssetUploadService requiere manager."
            );
        }

        this.manager = manager;
        this.maxBytes = maxBytes;
        this.uploader =
            typeof uploader === "function"
                ? uploader
                : null;
        this.deleter =
            typeof deleter === "function"
                ? deleter
                : null;
    }

    async importFiles(files) {
        const list =
            Array.from(files || []);

        const imported = [];
        const rejected = [];

        for (const file of list) {
            try {
                imported.push(
                    await this.importFile(
                        file
                    )
                );
            } catch (error) {
                rejected.push({
                    fileName:
                        file?.name || "archivo",
                    message:
                        error.message,
                });
            }
        }

        return {
            imported,
            rejected,
        };
    }

    async importFile(file) {
        validateFile(
            file,
            this.maxBytes
        );

        if (this.uploader) {
            const remoteAsset =
                await this.uploader(file);

            if (
                !remoteAsset
                || !remoteAsset.url
            ) {
                throw new Error(
                    "El servidor no devolvió un asset válido."
                );
            }

            return this.manager.register({
                ...remoteAsset,
                source:
                    ASSET_SOURCES.UPLOAD,
            });
        }

        const isVideo = file.type.startsWith("video/");
        const resourceUrl = isVideo
            ? await createVideoObjectUrl(file)
            : await readAsDataUrl(file);

        const metadata = file.type.startsWith("image/")
            ? await imageMetadata(resourceUrl, file)
            : isVideo
                ? await videoMetadata(resourceUrl, file)
                : { size: file.size };

        const type =
            typeFromMime(file.type);

        return this.manager.register({
            type,
            source:
                ASSET_SOURCES.UPLOAD,
            name:
                cleanName(file.name),
            category:
                categoryFromType(type),
            collection:
                "Mis archivos",
            url: resourceUrl,
            previewUrl: resourceUrl,
            mimeType: file.type,
            tags: [
                "upload",
                extensionOf(file.name),
            ].filter(Boolean),
            metadata,
        });
    }

    async removeAsset(assetId) {
        if (!this.deleter) {
            return {
                ok: true,
                localOnly: true,
            };
        }

        return this.deleter(assetId);
    }
}

function validateFile(
    file,
    maxBytes
) {
    if (!(file instanceof File)) {
        throw new TypeError(
            "Archivo inválido."
        );
    }

    if (
        !ACCEPTED_MIME_TYPES.has(
            file.type
        )
    ) {
        throw new Error(
            `Formato no permitido: ${file.type || "desconocido"}`
        );
    }

    if (file.size > maxBytes) {
        throw new Error(
            "El archivo supera el límite permitido."
        );
    }
}

function readAsDataUrl(file) {
    return new Promise(
        (resolve, reject) => {
            const reader =
                new FileReader();

            reader.addEventListener(
                "load",
                () =>
                    resolve(
                        String(reader.result)
                    )
            );

            reader.addEventListener(
                "error",
                () =>
                    reject(
                        new Error(
                            "No se pudo leer el archivo."
                        )
                    )
            );

            reader.readAsDataURL(file);
        }
    );
}

function createVideoObjectUrl(file) {
    if (globalThis.URL?.createObjectURL) {
        return globalThis.URL.createObjectURL(file);
    }

    return readAsDataUrl(file);
}

function videoMetadata(url, file) {
    return new Promise((resolve) => {
        if (typeof document === "undefined") {
            resolve({
                size: file.size,
                mediaKind: "VIDEO",
                volatileUrl: String(url).startsWith("blob:"),
            });
            return;
        }

        const video = document.createElement("video");
        video.preload = "metadata";
        video.muted = true;

        const finish = (extra = {}) => {
            resolve({
                width: Number(video.videoWidth || 0),
                height: Number(video.videoHeight || 0),
                duration: Number(video.duration || 0),
                size: file.size,
                mediaKind: "VIDEO",
                volatileUrl: String(url).startsWith("blob:"),
                ...extra,
            });
        };

        video.addEventListener("loadedmetadata", () => finish(), { once: true });
        video.addEventListener("error", () => finish({ metadataError: true }), { once: true });
        video.src = url;
    });
}

function imageMetadata(
    url,
    file
) {
    return new Promise(
        (resolve) => {
            const supportsAlpha =
                [
                    "image/png",
                    "image/webp",
                    "image/svg+xml",
                    "image/gif",
                ].includes(
                    file.type
                );

            const image =
                new Image();

            image.addEventListener(
                "load",
                () => {
                    resolve({
                        width:
                            image.naturalWidth,
                        height:
                            image.naturalHeight,
                        aspectRatio:
                            image.naturalWidth
                            / Math.max(
                                image.naturalHeight,
                                1
                            ),
                        size: file.size,
                        transparent:
                            supportsAlpha,
                        supportsAlpha,
                        animated:
                            file.type === "image/gif",
                        mediaKind: "IMAGE",
                    });
                }
            );

            image.addEventListener(
                "error",
                () => {
                    resolve({
                        size: file.size,
                        supportsAlpha,
                        animated:
                            file.type === "image/gif",
                        mediaKind: "IMAGE",
                    });
                }
            );

            image.src = url;
        }
    );
}

export function typeFromMime(mime) {
    if (
        mime.startsWith(
            "video/"
        )
    ) {
        return ASSET_TYPES.VIDEO;
    }

    if (
        mime.startsWith(
            "image/"
        )
    ) {
        return ASSET_TYPES.IMAGE;
    }

    return ASSET_TYPES.IMAGE;
}

export function categoryFromType(type) {
    if (
        type === ASSET_TYPES.VIDEO
    ) {
        return "Videos";
    }

    if (
        type
        === ASSET_TYPES.DECORATION
    ) {
        return "Decoraciones";
    }

    return "Fotografías";
}

function cleanName(name) {
    return String(name)
        .replace(
            /\.[^.]+$/,
            ""
        )
        .replace(
            /[_-]+/g,
            " "
        )
        .trim()
        || "Recurso";
}

function extensionOf(name) {
    return String(name)
        .split(".")
        .pop()
        ?.toLowerCase()
        || "";
}
