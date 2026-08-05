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

export class UniversalRenderer {
    constructor(options = {}) {
        this.options = {
            editable: false,
            device: "desktop",
            onNodeClick: null,
            assetResolver: null,
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

        if (
            this.options.editable
            && node.type !== NODE_TYPES.BACKGROUND
        ) {
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
        }

        return element;
    }

    createElementForNode(node) {
        const document =
            this.root.ownerDocument;

        const definition =
            getComponentDefinition(node.type);

        if (
            definition?.customRenderer
            === "countdown"
        ) {
            return this.createCountdownElement(
                document,
                node
            );
        }

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
                    node.content?.text || "";
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
                element.src =
                    node.content?.src || "";
                element.autoplay =
                    Boolean(
                        node.content?.autoplay
                    );
                element.loop =
                    Boolean(node.content?.loop);
                element.muted =
                    node.content?.muted !== false;
                element.playsInline = true;
                break;

            case NODE_TYPES.ICON:
                element.textContent =
                    node.content?.value || "•";
                break;

            case NODE_TYPES.MAP:
                element.textContent =
                    node.content?.placeholder
                    || "Mapa";
                break;

            case NODE_TYPES.GALLERY:
                element.dataset.r3Gallery = "1";
                break;

            case NODE_TYPES.RSVP:
                element.textContent =
                    node.content?.placeholder
                    || "RSVP";
                break;

            default:
                break;
        }
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

    createCountdownElement(document, node) {
        const wrapper =
            document.createElement("div");

        const labels =
            node.content?.labels
            || [
                "Días",
                "Horas",
                "Minutos",
                "Segundos",
            ];

        const values =
            node.content?.values
            || [0, 0, 0, 0];

        wrapper.classList.add(
            "r3-countdown"
        );

        const style = node.style || {};

        wrapper.style.setProperty(
            "--r3-countdown-value-size",
            `${Number(style.valueSize ?? 32)}px`
        );

        wrapper.style.setProperty(
            "--r3-countdown-label-size",
            `${Number(style.labelSize ?? 12)}px`
        );

        labels.forEach((label, index) => {
            const item =
                document.createElement("div");

            item.className =
                "r3-countdown__item";

            const value =
                document.createElement("strong");

            value.className =
                "r3-countdown__value";
            value.textContent =
                String(values[index] ?? 0);

            const caption =
                document.createElement("span");

            caption.className =
                "r3-countdown__label";
            caption.textContent = label;

            item.append(value, caption);
            wrapper.append(item);
        });

        return wrapper;
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