import {
    NODE_TYPES,
    LAYOUT_MODES,
    componentElementName,
    getComponentDefinition,
    normalizeDocument,
    validateDocument,
} from "../core/index.js";

import {
    effectiveLayoutMode,
} from "../canvas/transform_policy.js";

import {
    normalizeMapSource,
} from "../components/map.js";

import {
    normalizeVideoSource,
} from "../components/video.js";

import {
    INTERACTION_TRIGGERS,
    InteractionEngine,
} from "../interaction/index.js";

export class UniversalRenderer {
    constructor(options = {}) {
        this.options = {
            editable: false,
            device: "desktop",
            onNodeClick: null,
            onInteractionResult: null,
            onInteractionError: null,
            assetResolver: null,
            interactionEngine:
                new InteractionEngine(),
            ...options,
        };

        this.document = null;
        this.root = null;
        this.nodeMap = new Map();
    }

    mount(root, document) {
        if (!(root instanceof Element)) {
            throw new TypeError(
                "root debe ser un elemento HTML válido."
            );
        }

        const normalized = normalizeDocument(document);
        const validation = validateDocument(normalized);

        if (!validation.valid) {
            throw new Error(
                validation.errors.join("\n")
            );
        }

        this.root = root;

        this.options.interactionEngine
            ?.runtime
            ?.setDocumentRoot?.(root);

        this.document = normalized;
        this.nodeMap = new Map(
            [
                ...normalized.sections,
                ...normalized.nodes,
            ].map((node) => [node.id, node])
        );

        this.render();

        return this;
    }

    update(document) {
        if (!this.root) {
            throw new Error(
                "El renderer no está montado."
            );
        }

        return this.mount(this.root, document);
    }

    setDevice(device) {
        this.options.device = device;
        this.render();
    }

    setEditable(editable) {
        this.options.editable = Boolean(editable);
        this.render();
    }

    render() {
        if (!this.root || !this.document) {
            return;
        }

        this.root.replaceChildren();
        this.root.classList.add("r3-page");
        this.root.dataset.r3Device =
            this.options.device;
        this.root.dataset.r3Editable =
            this.options.editable ? "1" : "0";

        const fragment =
            this.root.ownerDocument
                .createDocumentFragment();

        const sections = [
            ...this.document.sections,
        ].sort((a, b) => a.order - b.order);

        for (const section of sections) {
            if (!section.visible) continue;

            fragment.append(
                this.renderNode(section)
            );
        }

        this.root.append(fragment);
    }

    renderNode(node) {
        const element =
            this.createElementForNode(node);

        this.applyCommonAttributes(
            element,
            node
        );

        this.applyLayout(
            element,
            node
        );

        this.applyAppearance(
            element,
            node
        );

        this.applyContent(
            element,
            node
        );

        const children = this.childrenOf(node);

        for (const child of children) {
            if (!child.visible) continue;

            element.append(
                this.renderNode(child)
            );
        }

        this.bindNodeEvents(
            element,
            node
        );

        return element;
    }

    bindNodeEvents(element, node) {
        if (node.type === NODE_TYPES.BACKGROUND) {
            return;
        }

        if (this.options.editable) {
            element.addEventListener(
                "click",
                (event) => {
                    event.stopPropagation();

                    this.options.onNodeClick?.(
                        node,
                        element,
                        event
                    );
                }
            );

            return;
        }

        if (!node.interaction?.enabled) {
            return;
        }

        element.dataset.r3Interactive = "1";

        element.addEventListener(
            "click",
            (event) => {
                event.preventDefault();
                event.stopPropagation();

                this.executeInteraction(
                    node,
                    event
                );
            }
        );
    }

    executeInteraction(node, event = null) {
        const engine =
            this.options.interactionEngine;

        if (
            !engine
            || typeof engine.execute
                !== "function"
        ) {
            throw new Error(
                "UniversalRenderer requiere un InteractionEngine válido."
            );
        }

        try {
            const result = engine.execute(
                node,
                {
                    trigger:
                        INTERACTION_TRIGGERS.CLICK,
                    event,
                    document: this.document,
                    metadata: {
                        device:
                            this.options.device,
                        editable:
                            this.options.editable,
                    },
                }
            );

            this.options
                .onInteractionResult?.(
                    result,
                    {
                        node,
                        event,
                        renderer: this,
                    }
                );

            return result;
        } catch (error) {
            this.options
                .onInteractionError?.(
                    error,
                    {
                        node,
                        event,
                        renderer: this,
                    }
                );

            return {
                handled: false,
                status: "error",
                reason: "interaction-error",
                nodeId: node?.id || null,
                error,
            };
        }
    }

    createElementForNode(node) {
        const document =
            this.root.ownerDocument;

        const definition =
            getComponentDefinition(node.type);


        if (node.type === NODE_TYPES.TEXT) {
            return document.createElement(
                safeTextTag(node.content?.tag)
            );
        }

        return document.createElement(
            componentElementName(node.type)
        );
    }

    applyCommonAttributes(element, node) {
        element.classList.add(
            "r3-node",
            `r3-node--${node.type.toLowerCase()}`
        );

        element.dataset.r3NodeId = node.id;
        element.dataset.r3NodeType = node.type;
        element.dataset.r3LayoutMode =
            effectiveLayoutMode(node);
        element.dataset.r3CoordinateSpace =
            node.coordinateSpace;

        if (node.type === NODE_TYPES.SECTION) {
            element.dataset.r3SectionId =
                node.id;
        }

        if (node.locked) {
            element.dataset.r3Locked = "1";
        }

        if (!node.visible) {
            element.hidden = true;
        }

        if (node.name) {
            element.setAttribute(
                "aria-label",
                node.name
            );
        }
    }

    applyLayout(element, node) {
        const style =
            this.resolveResponsiveValue(
                node,
                "style"
            );

        element.style.setProperty(
            "--r3-x",
            `${Number(node.x ?? 50)}%`
        );

        element.style.setProperty(
            "--r3-y",
            `${Number(node.y ?? 50)}%`
        );

        const structuralSection =
            node.type === NODE_TYPES.SECTION;

        element.style.setProperty(
            "--r3-width",
            structuralSection
                ? "100%"
                : dimensionToCss(
                    node.width,
                    "%"
                )
        );

        element.style.setProperty(
            "--r3-height",
            dimensionToCss(
                node.height,
                structuralSection ? "px" : "%"
            )
        );

        element.style.setProperty(
            "--r3-min-height",
            dimensionToCss(
                node.minHeight,
                "px"
            )
        );

        element.style.setProperty(
            "--r3-max-height",
            Number(node.maxHeight || 0) > 0
                ? `${Number(node.maxHeight)}px`
                : "none"
        );

        element.style.setProperty(
            "--r3-rotation",
            `${Number(node.rotation || 0)}deg`
        );

        element.style.setProperty(
            "--r3-scale",
            Number(node.scale ?? 1)
        );

        element.style.setProperty(
            "--r3-flip-x",
            style.flipX ? -1 : 1
        );

        element.style.setProperty(
            "--r3-flip-y",
            style.flipY ? -1 : 1
        );

        element.style.setProperty(
            "--r3-opacity",
            Number(node.opacity ?? 1)
        );

        element.style.setProperty(
            "--r3-z",
            Number(node.zIndex ?? 1)
        );

        element.style.setProperty(
            "--r3-padding-x",
            `${Number(style.paddingX ?? 0)}px`
        );

        element.style.setProperty(
            "--r3-padding-y",
            `${Number(style.paddingY ?? 0)}px`
        );

        element.style.setProperty(
            "--r3-gap",
            `${Number(style.gap ?? 0)}px`
        );

        element.style.setProperty(
            "--r3-direction",
            mapDirection(style.direction)
        );

        element.style.setProperty(
            "--r3-align",
            style.align || "stretch"
        );

        element.style.setProperty(
            "--r3-justify",
            style.justify || "start"
        );

        if (style.maxWidth) {
            element.style.setProperty(
                "--r3-content-max-width",
                `${Number(style.maxWidth)}px`
            );
        }

        if (style.overflow) {
            element.style.overflow =
                style.overflow;
        }

        const layoutMode =
            effectiveLayoutMode(node);

        if (
            layoutMode === LAYOUT_MODES.FLOW
        ) {
            element.classList.add(
                "r3-layout-flow"
            );
        }

        if (
            layoutMode
            === LAYOUT_MODES.ABSOLUTE
        ) {
            element.classList.add(
                "r3-layout-absolute"
            );
        }

        if (
            layoutMode === LAYOUT_MODES.LAYER
        ) {
            element.classList.add(
                "r3-layout-layer"
            );
        }
    }

    applyAppearance(element, node) {
        const style =
            this.resolveResponsiveValue(
                node,
                "style"
            );

        if (style.backgroundColor) {
            element.style.backgroundColor =
                style.backgroundColor;
        }

        if (style.color) {
            element.style.color =
                style.color;
        }

        if (style.borderColor) {
            element.style.borderColor =
                style.borderColor;
        }

        if (style.borderWidth !== undefined) {
            element.style.borderWidth =
                `${Number(style.borderWidth)}px`;
            element.style.borderStyle =
                style.borderStyle || "solid";
        }

        if (style.borderRadius !== undefined) {
            element.style.borderRadius =
                `${Number(style.borderRadius)}px`;
        }

        if (style.boxShadow) {
            element.style.boxShadow =
                style.boxShadow;
        }

        if (style.objectFit) {
            element.style.objectFit =
                style.objectFit;
        }

        if (style.objectPosition) {
            element.style.objectPosition =
                style.objectPosition;
        }

        if (
            node.type !== NODE_TYPES.BACKGROUND
            && (
                style.brightness !== undefined
                || style.contrast !== undefined
                || style.saturation !== undefined
                || style.blur !== undefined
            )
        ) {
            element.style.filter = [
                `brightness(${Number(style.brightness ?? 1)})`,
                `contrast(${Number(style.contrast ?? 1)})`,
                `saturate(${Number(style.saturation ?? 1)})`,
                `blur(${Number(style.blur ?? 0)}px)`,
            ].join(" ");
        }

        if (style.fontFamily) {
            element.style.fontFamily =
                style.fontFamily;
        }

        if (style.fontSize !== undefined) {
            element.style.fontSize =
                `${Number(style.fontSize)}px`;
        }

        if (style.fontWeight !== undefined) {
            element.style.fontWeight =
                String(style.fontWeight);
        }

        if (style.textAlign) {
            element.style.textAlign =
                style.textAlign;
        }

        if (style.lineHeight !== undefined) {
            element.style.lineHeight =
                String(style.lineHeight);
        }

        if (style.letterSpacing !== undefined) {
            element.style.letterSpacing =
                `${Number(style.letterSpacing)}px`;
        }

        if (node.type === NODE_TYPES.SEPARATOR) {
            const orientation = style.orientation === "vertical"
                ? "vertical"
                : "horizontal";
            const thickness = Math.max(Number(style.borderWidth ?? 1), 1);
            element.dataset.r3Orientation = orientation;
            element.style.backgroundColor = style.color || "currentColor";
            element.style.borderRadius = `${Number(style.borderRadius ?? 0)}px`;
            if (orientation === "vertical") {
                element.style.width = `${thickness}px`;
            } else {
                element.style.height = `${thickness}px`;
            }
        }

        if (node.type === NODE_TYPES.BACKGROUND) {
            this.applyBackground(
                element,
                node,
                style
            );
        }
    }

    applyContent(element, node) {
        switch (node.type) {
            case NODE_TYPES.TEXT:
                element.textContent =
                    this.resolveTextContent(node);
                if (node.style?.textTransform) {
                    element.style.textTransform = node.style.textTransform;
                }
                break;

            case NODE_TYPES.IMAGE:
            case NODE_TYPES.DECORATION:
                element.src =
                    this.resolveAssetUrl(node);
                element.alt =
                    node.content?.alt || node.name;
                element.loading =
                    node.content?.loading || "lazy";
                element.draggable = false;
                break;

            case NODE_TYPES.BUTTON:
                element.textContent =
                    node.content?.label
                    || "Botón";
                element.href =
                    node.content?.href || "#";
                break;

            case NODE_TYPES.VIDEO:
                this.applyVideoContent(element, node);
                break;

            case NODE_TYPES.ICON:
                element.textContent =
                    node.content?.value || "•";
                break;

            case NODE_TYPES.MAP:
                this.applyMapContent(element, node);
                break;

            case NODE_TYPES.GALLERY:
                element.dataset.r3Gallery = "1";
                break;

            case NODE_TYPES.RSVP:
                element.textContent =
                    node.content?.placeholder
                    || "RSVP";
                break;

            case NODE_TYPES.SEPARATOR:
                element.setAttribute("aria-hidden", "true");
                break;

            default:
                break;
        }
    }

    applyVideoContent(element, node) {
        const content = node.content || {};
        const source = normalizeVideoSource(
            content.source || content.src || "",
            {
                sourceType: content.sourceType || "auto",
                autoplay: Boolean(content.autoplay),
                loop: Boolean(content.loop),
                muted: content.muted !== false,
                controls: content.controls !== false,
            }
        );

        element.replaceChildren();
        element.dataset.r3VideoState = source.valid
            ? source.kind
            : "invalid";

        if (!source.valid) {
            const fallback = element.ownerDocument.createElement("div");
            fallback.className = "r3-video-fallback";
            const title = element.ownerDocument.createElement("strong");
            title.textContent = "Configura una fuente de video válida";
            const detail = element.ownerDocument.createElement("small");
            detail.textContent = source.reason || "Usa una URL de YouTube o un video directo.";
            fallback.append(title, detail);
            element.append(fallback);
            return;
        }

        if (source.kind === "youtube") {
            const iframe = element.ownerDocument.createElement("iframe");
            iframe.className = "r3-video-frame r3-video-frame--youtube";
            iframe.src = source.embedUrl;
            iframe.title = content.title || node.name || "Video de YouTube";
            iframe.loading = content.loading === "eager" ? "eager" : "lazy";
            iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
            iframe.allowFullscreen = true;
            iframe.referrerPolicy = "strict-origin-when-cross-origin";
            iframe.setAttribute("tabindex", this.options.editable ? "-1" : "0");
            if (this.options.editable) iframe.style.pointerEvents = "none";
            element.append(iframe);
            return;
        }

        const video = element.ownerDocument.createElement("video");
        video.className = "r3-video-frame r3-video-frame--direct";
        video.src = source.source;
        video.autoplay = Boolean(content.autoplay) && !this.options.editable;
        video.loop = Boolean(content.loop);
        video.muted = content.muted !== false;
        video.controls = content.controls !== false && !this.options.editable;
        video.playsInline = content.playsInline !== false;
        video.preload = content.loading === "eager" ? "auto" : "metadata";
        if (content.poster) video.poster = String(content.poster);
        video.setAttribute("aria-label", content.title || node.name || "Video");
        if (this.options.editable) video.style.pointerEvents = "none";
        element.append(video);
    }

    applyMapContent(element, node) {
        const source = normalizeMapSource(
            node.content?.source || "",
            { zoom: node.content?.zoom ?? 15 }
        );

        element.replaceChildren();
        element.dataset.r3MapState = source.valid
            ? source.kind
            : "invalid";

        if (!source.valid || !source.embedUrl) {
            const fallback = element.ownerDocument.createElement("div");
            fallback.className = "r3-map-fallback";

            const title = element.ownerDocument.createElement("strong");
            title.textContent = source.valid
                ? "Abrir ubicación en Google Maps"
                : "Configura una ubicación válida";

            const detail = element.ownerDocument.createElement("small");
            detail.textContent = source.valid
                ? "Este enlace corto no se puede embeber directamente."
                : "Usa coordenadas, una dirección, una URL de Maps o un iframe.";

            fallback.append(title, detail);

            if (source.externalUrl && !this.options.editable) {
                fallback.tabIndex = 0;
                fallback.setAttribute("role", "link");
                fallback.addEventListener("click", () => {
                    globalThis.open?.(
                        source.externalUrl,
                        "_blank",
                        "noopener,noreferrer"
                    );
                });
            }

            element.append(fallback);
            return;
        }

        const iframe = element.ownerDocument.createElement("iframe");
        iframe.className = "r3-map-frame";
        iframe.src = source.embedUrl;
        iframe.title = node.content?.title || node.name || "Google Maps";
        iframe.loading = node.content?.loading === "eager" ? "eager" : "lazy";
        iframe.referrerPolicy = "no-referrer-when-downgrade";
        iframe.allowFullscreen = true;
        iframe.setAttribute("aria-label", iframe.title);
        iframe.setAttribute("tabindex", this.options.editable ? "-1" : "0");

        if (this.options.editable) {
            iframe.style.pointerEvents = "none";
            element.dataset.r3MapEditable = "1";
        }

        element.append(iframe);
    }

    applyBackground(element, node, style) {
        const assetUrl =
            this.resolveAssetUrl(node);

        if (style.color) {
            element.style.backgroundColor =
                style.color;
        }

        if (assetUrl) {
            element.style.backgroundImage =
                `url("${cssEscapeUrl(assetUrl)}")`;
        } else {
            element.style.backgroundImage =
                "none";
        }

        const fit =
            backgroundFit(style.fit);

        const zoom =
            Math.max(
                Number(style.zoom ?? 1),
                0.01
            );

        if (
            zoom !== 1
            && fit !== "auto"
        ) {
            element.style.backgroundSize =
                `${100 * zoom}% auto`;
        } else {
            element.style.backgroundSize =
                fit;
        }

        element.style.backgroundPosition =
            `${Number(style.positionX ?? node.x ?? 50)}% `
            + `${Number(style.positionY ?? node.y ?? 50)}%`;

        element.style.backgroundRepeat =
            style.repeat || "no-repeat";

        element.style.filter = [
            `brightness(${Number(style.brightness ?? 1)})`,
            `contrast(${Number(style.contrast ?? 1)})`,
            `saturate(${Number(style.saturation ?? 1)})`,
            `blur(${Number(style.blur ?? 0)}px)`,
        ].join(" ");
    }

    resolveAssetUrl(node) {
        const assetId =
            node.content?.assetId
            || node.content?.asset?.id
            || null;

        if (
            assetId
            && typeof this.options.assetResolver
                === "function"
        ) {
            const resolved =
                this.options.assetResolver(
                    assetId,
                    node
                );

            if (resolved) {
                return String(resolved);
            }
        }

        const asset =
            node.content?.asset;

        if (typeof asset === "string") {
            return asset;
        }

        if (asset?.url) {
            return String(asset.url);
        }

        return String(
            node.content?.src || ""
        );
    }

    resolveTextContent(node) {
        const binding = node.content?.binding;

        if (binding?.source !== "COUNTDOWN") {
            return node.content?.text || "";
        }

        const countdown = this.findAncestorByType(
            node,
            NODE_TYPES.COUNTDOWN
        );

        if (!countdown) {
            return node.content?.text || "";
        }

        const unitIndex = {
            days: 0,
            hours: 1,
            minutes: 2,
            seconds: 3,
        }[binding.unit];

        if (unitIndex === undefined) {
            return node.content?.text || "";
        }

        if (binding.role === "label") {
            return String(node.content?.text ?? "");
        }

        return String(
            countdown.content?.values?.[unitIndex]
            ?? node.content?.text
            ?? 0
        );
    }

    findAncestorByType(node, type) {
        let current = node;

        while (current?.parentId) {
            current = this.nodeMap.get(current.parentId);
            if (current?.type === type) return current;
        }

        return null;
    }

    childrenOf(node) {
        return (node.children || [])
            .map((id) => this.nodeMap.get(id))
            .filter(Boolean)
            .sort((a, b) => a.order - b.order);
    }

    resolveResponsiveValue(node, key) {
        const base =
            node[key]
            && typeof node[key] === "object"
                ? node[key]
                : {};

        const responsive =
            node.responsive || {};

        const device =
            this.options.device;

        if (
            !responsive[device]
            || !responsive[device][key]
        ) {
            return structuredCloneSafe(base);
        }

        return {
            ...structuredCloneSafe(base),
            ...structuredCloneSafe(
                responsive[device][key]
            ),
        };
    }
}

function mapDirection(value) {
    if (value === "row") return "row";
    if (value === "grid") return "row";
    return "column";
}


function safeTextTag(value) {
    const tag = String(value || "p").toLowerCase();
    return ["p", "h1", "h2", "h3", "span"].includes(tag)
        ? tag
        : "p";
}

function dimensionToCss(value, unit) {
    if (value === "auto") return "auto";

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "auto";
    }

    if (number === 0) {
        return "0";
    }

    return `${number}${unit}`;
}

function backgroundFit(value) {
    if (value === "contain") return "contain";
    if (value === "original") return "auto";
    return "cover";
}

function cssEscapeUrl(value) {
    return String(value)
        .replaceAll("\\", "\\\\")
        .replaceAll('"', '\\"')
        .replaceAll("\n", "");
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}