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
    ]);

export class AssetUploadService {
    constructor(options = {}) {
        const {
            manager,
            maxBytes =
                12 * 1024 * 1024,
        } = options;

        if (!manager) {
            throw new Error(
                "AssetUploadService requiere manager."
            );
        }

        this.manager = manager;
        this.maxBytes = maxBytes;
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

        const dataUrl =
            await readAsDataUrl(file);

        const metadata =
            file.type.startsWith(
                "image/"
            )
                ? await imageMetadata(
                    dataUrl,
                    file
                )
                : {
                    size: file.size,
                };

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
            url: dataUrl,
            previewUrl: dataUrl,
            mimeType: file.type,
            tags: [
                "upload",
                extensionOf(file.name),
            ].filter(Boolean),
            metadata,
        });
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

function imageMetadata(
    url,
    file
) {
    return new Promise(
        (resolve) => {
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
                            [
                                "image/png",
                                "image/webp",
                                "image/svg+xml",
                                "image/gif",
                            ].includes(
                                file.type
                            ),
                    });
                }
            );

            image.addEventListener(
                "error",
                () => {
                    resolve({
                        size: file.size,
                    });
                }
            );

            image.src = url;
        }
    );
}

function typeFromMime(mime) {
    if (
        mime.startsWith(
            "video/"
        )
    ) {
        return ASSET_TYPES.VIDEO;
    }

    if (
        mime === "image/svg+xml"
        || mime === "image/png"
        || mime === "image/webp"
        || mime === "image/gif"
    ) {
        return ASSET_TYPES.DECORATION;
    }

    return ASSET_TYPES.IMAGE;
}

function categoryFromType(type) {
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
