import {
    ASSET_SOURCES,
} from "./asset_manager.js";

const VIEWS = Object.freeze({
    ALL: "ALL",
    RECENT: "RECENT",
    FAVORITES: "FAVORITES",
    UPLOADS: "UPLOADS",
});

export class AssetLibrary {
    constructor(options = {}) {
        const {
            root,
            manager,
            uploadService = null,
            onUse = null,
            onStatus = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "AssetLibrary root debe ser un elemento HTML."
            );
        }

        if (!manager) {
            throw new Error(
                "AssetLibrary requiere manager."
            );
        }

        this.root = root;
        this.manager = manager;
        this.uploadService =
            uploadService;
        this.onUse = onUse;
        this.onStatus = onStatus;

        this.state = {
            query: "",
            view: VIEWS.ALL,
            category: "Todos",
        };

        this.unsubscribe =
            this.manager.subscribe(
                () => this.render()
            );

        this.render();
    }

    destroy() {
        this.unsubscribe?.();
        this.root.replaceChildren();
    }

    render() {
        this.root.replaceChildren();
        this.root.classList.add(
            "r3-asset-library"
        );

        this.root.append(
            this.#renderHeader(),
            this.#renderPrimaryNav(),
            this.#renderCategories(),
            this.#renderSummary(),
            this.#renderGrid()
        );
    }

    #renderHeader() {
        const header =
            document.createElement(
                "header"
            );

        header.className =
            "r3-asset-library__header";

        const heading =
            document.createElement("div");

        heading.innerHTML = `
            <strong>Design Studio</strong>
            <small>Recursos visuales del proyecto</small>
        `;

        const uploadButton =
            document.createElement(
                "button"
            );

        uploadButton.type = "button";
        uploadButton.className =
            "r3-asset-library__upload";
        uploadButton.textContent =
            "Subir";

        const fileInput =
            document.createElement(
                "input"
            );

        fileInput.type = "file";
        fileInput.multiple = true;
        fileInput.hidden = true;
        fileInput.accept =
            "image/*,video/mp4,video/webm,video/ogg,video/quicktime,video/x-m4v,audio/mpeg,audio/mp4,audio/x-m4a,audio/ogg,audio/wav,audio/x-wav,.mov,.m4v,.ogv,.mp3,.m4a,.wav,.ogg";

        uploadButton.addEventListener(
            "click",
            () => fileInput.click()
        );

        fileInput.addEventListener(
            "change",
            async () => {
                await this.#importFiles(
                    fileInput.files
                );

                fileInput.value = "";
            }
        );

        const top =
            document.createElement("div");

        top.className =
            "r3-asset-library__top";

        top.append(
            heading,
            uploadButton,
            fileInput
        );

        const search =
            document.createElement(
                "input"
            );

        search.type = "search";
        search.placeholder =
            "Buscar imágenes, videos, fondos...";
        search.value =
            this.state.query;

        search.addEventListener(
            "input",
            () => {
                this.state.query =
                    search.value;
                this.render();
            }
        );

        header.append(top, search);
        return header;
    }

    #renderPrimaryNav() {
        const items = [
            [VIEWS.ALL, "Todos"],
            [VIEWS.RECENT, "Recientes"],
            [VIEWS.FAVORITES, "Favoritos"],
            [VIEWS.UPLOADS, "Mis archivos"],
        ];

        const nav =
            document.createElement("nav");

        nav.className =
            "r3-asset-library__views";

        for (
            const [value, label]
            of items
        ) {
            const button =
                document.createElement(
                    "button"
                );

            button.type = "button";
            button.textContent = label;
            button.classList.toggle(
                "is-active",
                this.state.view === value
            );

            button.addEventListener(
                "click",
                () => {
                    this.state.view =
                        value;
                    this.state.category =
                        "Todos";
                    this.render();
                }
            );

            nav.append(button);
        }

        return nav;
    }

    #renderCategories() {
        const categories = [
            "Todos",
            ...this.manager.categories(),
        ];

        const nav =
            document.createElement("nav");

        nav.className =
            "r3-asset-library__categories";

        for (
            const category
            of categories
        ) {
            const button =
                document.createElement(
                    "button"
                );

            button.type = "button";
            button.textContent =
                category;
            button.classList.toggle(
                "is-active",
                this.state.category
                === category
            );

            button.addEventListener(
                "click",
                () => {
                    this.state.category =
                        category;
                    this.render();
                }
            );

            nav.append(button);
        }

        return nav;
    }

    #renderSummary() {
        const assets =
            this.#filteredAssets();

        const summary =
            document.createElement("div");

        summary.className =
            "r3-asset-library__summary";

        summary.textContent =
            `${assets.length} recurso`
            + (
                assets.length === 1
                    ? ""
                    : "s"
            );

        return summary;
    }

    #renderGrid() {
        const assets =
            this.#filteredAssets();

        const grid =
            document.createElement("div");

        grid.className =
            "r3-asset-library__grid";

        grid.addEventListener(
            "dragover",
            (event) => {
                if (
                    event.dataTransfer
                        ?.types
                        .includes("Files")
                ) {
                    event.preventDefault();
                    grid.classList.add(
                        "is-file-drop"
                    );
                }
            }
        );

        grid.addEventListener(
            "dragleave",
            () => {
                grid.classList.remove(
                    "is-file-drop"
                );
            }
        );

        grid.addEventListener(
            "drop",
            async (event) => {
                if (
                    !event.dataTransfer
                        ?.files?.length
                ) {
                    return;
                }

                event.preventDefault();
                grid.classList.remove(
                    "is-file-drop"
                );

                await this.#importFiles(
                    event.dataTransfer.files
                );
            }
        );

        if (!assets.length) {
            const empty =
                document.createElement("div");

            empty.className =
                "r3-asset-library__empty";

            empty.innerHTML = `
                <strong>No hay recursos</strong>
                <span>
                    Cambia los filtros o sube un archivo.
                </span>
            `;

            grid.append(empty);
            return grid;
        }

        for (const asset of assets) {
            grid.append(
                this.#renderAsset(asset)
            );
        }

        return grid;
    }

    #renderAsset(asset) {
        const card =
            document.createElement(
                "article"
            );

        card.className =
            "r3-asset-card";
        card.draggable = true;
        card.dataset.assetId =
            asset.id;

        const preview =
            document.createElement(
                "button"
            );

        preview.type = "button";
        preview.className =
            "r3-asset-card__preview";
        preview.title =
            `Agregar ${asset.name}`;

        const media =
            createPreview(asset);

        preview.append(media);

        const badge =
            document.createElement(
                "span"
            );

        badge.className =
            "r3-asset-card__badge";
        badge.textContent =
            asset.category;

        preview.append(badge);

        const footer =
            document.createElement(
                "footer"
            );

        const text =
            document.createElement("div");

        const name =
            document.createElement(
                "strong"
            );

        name.textContent =
            asset.name;

        const collection =
            document.createElement(
                "small"
            );

        collection.textContent =
            asset.collection;

        text.append(
            name,
            collection
        );

        const actions =
            document.createElement("div");

        actions.className =
            "r3-asset-card__actions";

        const inspect =
            document.createElement(
                "button"
            );

        inspect.type = "button";
        inspect.className =
            "r3-asset-card__inspect";
        inspect.textContent = "Ver";
        inspect.title =
            "Ver recurso";
        inspect.setAttribute(
            "aria-label",
            `Ver ${asset.name}`
        );

        inspect.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();
                this.#openAssetDetail(
                    asset
                );
            }
        );

        const favorite =
            document.createElement(
                "button"
            );

        favorite.type = "button";
        favorite.className =
            "r3-asset-card__favorite";
        favorite.textContent =
            asset.favorite ? "★" : "☆";
        favorite.title =
            "Favorito";

        favorite.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                this.manager
                    .toggleFavorite(
                        asset.id
                    );
            }
        );

        actions.append(
            inspect,
            favorite
        );

        if (
            asset.source
            !== ASSET_SOURCES.BUILTIN
        ) {
            const remove =
                document.createElement(
                    "button"
                );

            remove.type = "button";
            remove.className =
                "r3-asset-card__remove";
            remove.textContent = "×";
            remove.title =
                "Eliminar recurso";

            remove.addEventListener(
                "click",
                async (event) => {
                    event.stopPropagation();
                    remove.disabled = true;

                    try {
                        await this.#removeAsset(
                            asset
                        );
                    } finally {
                        remove.disabled = false;
                    }
                }
            );

            actions.append(remove);
        }

        footer.append(
            text,
            actions
        );

        card.append(
            preview,
            footer
        );

        preview.addEventListener(
            "click",
            () =>
                this.#useAsset(asset)
        );

        card.addEventListener(
            "dragstart",
            (event) => {
                event.dataTransfer
                    ?.setData(
                        "application/x-r3-asset",
                        asset.id
                    );

                event.dataTransfer
                    ?.setData(
                        "text/plain",
                        asset.id
                    );

                if (event.dataTransfer) {
                    event.dataTransfer
                        .effectAllowed =
                            "copy";
                }
            }
        );

        return card;
    }

    #openAssetDetail(asset) {
        const dialog =
            document.createElement(
                "dialog"
            );

        dialog.className =
            "r3-asset-detail";

        const shell =
            document.createElement(
                "div"
            );

        shell.className =
            "r3-asset-detail__shell";

        const header =
            document.createElement(
                "header"
            );

        header.className =
            "r3-asset-detail__header";

        const heading =
            document.createElement(
                "div"
            );

        const name =
            document.createElement(
                "strong"
            );
        name.textContent = asset.name;

        const meta =
            document.createElement(
                "small"
            );
        meta.textContent =
            [
                asset.category,
                asset.collection,
                asset.mimeType,
            ]
                .filter(Boolean)
                .join(" · ");

        heading.append(name, meta);

        const close =
            document.createElement(
                "button"
            );
        close.type = "button";
        close.className =
            "r3-asset-detail__close";
        close.textContent = "Cerrar";
        close.addEventListener(
            "click",
            () => dialog.close()
        );

        header.append(heading, close);

        const media =
            document.createElement(
                "div"
            );
        media.className =
            "r3-asset-detail__media";
        media.append(
            createDetailPreview(asset)
        );

        const footer =
            document.createElement(
                "footer"
            );
        footer.className =
            "r3-asset-detail__footer";

        const use =
            document.createElement(
                "button"
            );
        use.type = "button";
        use.className =
            "r3-asset-detail__use";
        use.textContent = "Usar recurso";
        use.addEventListener(
            "click",
            () => {
                this.#useAsset(asset);
                dialog.close();
            }
        );

        footer.append(use);

        if (
            asset.source
            !== ASSET_SOURCES.BUILTIN
        ) {
            const remove =
                document.createElement(
                    "button"
                );
            remove.type = "button";
            remove.className =
                "r3-asset-detail__delete";
            remove.textContent =
                "Eliminar recurso";
            remove.addEventListener(
                "click",
                async () => {
                    remove.disabled = true;
                    const deleted =
                        await this.#removeAsset(
                            asset
                        );
                    remove.disabled = false;

                    if (deleted) {
                        dialog.close();
                    }
                }
            );
            footer.append(remove);
        }

        shell.append(
            header,
            media,
            footer
        );
        dialog.append(shell);

        dialog.addEventListener(
            "close",
            () => dialog.remove(),
            { once: true }
        );

        document.body.append(dialog);

        if (
            typeof dialog.showModal
            === "function"
        ) {
            dialog.showModal();
        } else {
            dialog.setAttribute(
                "open",
                ""
            );
        }
    }

    async #removeAsset(asset) {
        const confirmed =
            globalThis.confirm
                ? globalThis.confirm(
                    `¿Eliminar "${asset.name}"?`
                )
                : true;

        if (!confirmed) {
            return false;
        }

        if (!this.uploadService) {
            this.onStatus?.(
                "La eliminación remota no está configurada."
            );
            return false;
        }

        try {
            await this.uploadService
                .removeAsset(asset.id);

            this.manager.remove(
                asset.id
            );

            this.onStatus?.(
                `${asset.name} eliminado`
            );
            return true;
        } catch (error) {
            this.onStatus?.(
                error?.message
                || "No se pudo eliminar el recurso."
            );
            return false;
        }
    }

    #filteredAssets() {
        const filters = {
            query:
                this.state.query,
        };

        if (
            this.state.category
            !== "Todos"
        ) {
            filters.category =
                this.state.category;
        }

        if (
            this.state.view
            === VIEWS.RECENT
        ) {
            filters.recent = true;
        }

        if (
            this.state.view
            === VIEWS.FAVORITES
        ) {
            filters.favorite = true;
        }

        if (
            this.state.view
            === VIEWS.UPLOADS
        ) {
            filters.source =
                ASSET_SOURCES.UPLOAD;
        }

        return this.manager.list(
            filters
        );
    }

    #useAsset(asset) {
        const used =
            this.manager.use(
                asset.id
            );

        this.onUse?.(
            used || asset
        );

        this.onStatus?.(
            `${asset.name} agregado`
        );
    }

    async #importFiles(files) {
        if (!this.uploadService) {
            this.onStatus?.(
                "La carga de archivos no está configurada."
            );
            return;
        }

        const result =
            await this.uploadService
                .importFiles(files);

        if (
            result.imported.length
        ) {
            this.state.view =
                VIEWS.UPLOADS;
            this.state.category =
                "Todos";
        }

        const messages = [];

        if (
            result.imported.length
        ) {
            messages.push(
                `${result.imported.length} archivo(s) importado(s)`
            );
        }

        if (
            result.rejected.length
        ) {
            messages.push(
                `${result.rejected.length} rechazado(s)`
            );
        }

        this.onStatus?.(
            messages.join(" · ")
            || "Sin archivos"
        );

        this.render();
    }
}

function createPreview(asset) {
    if (
        asset.mimeType
            .startsWith("video/")
    ) {
        const video =
            document.createElement(
                "video"
            );

        video.src = asset.previewUrl
            || asset.url;
        video.muted = true;
        video.playsInline = true;
        video.preload = "metadata";

        return video;
    }

    if (
        asset.mimeType
            .startsWith("audio/")
    ) {
        const preview =
            document.createElement(
                "div"
            );
        preview.className =
            "r3-asset-card__audio-preview";

        const icon =
            document.createElement(
                "span"
            );
        icon.textContent = "♫";

        const label =
            document.createElement(
                "span"
            );
        label.textContent = asset.name;

        preview.append(icon, label);
        return preview;
    }

    const image =
        document.createElement("img");

    image.src =
        asset.previewUrl
        || asset.url;
    image.alt = asset.name;
    image.loading = "lazy";

    return image;
}

function createDetailPreview(asset) {
    if (
        asset.mimeType
            .startsWith("video/")
    ) {
        const video =
            document.createElement(
                "video"
            );
        video.src = asset.url
            || asset.previewUrl;
        video.controls = true;
        video.playsInline = true;
        video.preload = "metadata";
        return video;
    }

    if (
        asset.mimeType
            .startsWith("audio/")
    ) {
        const audio =
            document.createElement(
                "audio"
            );
        audio.src = asset.url;
        audio.controls = true;
        audio.preload = "metadata";
        return audio;
    }

    const image =
        document.createElement("img");
    image.src = asset.url
        || asset.previewUrl;
    image.alt = asset.name;
    return image;
}
