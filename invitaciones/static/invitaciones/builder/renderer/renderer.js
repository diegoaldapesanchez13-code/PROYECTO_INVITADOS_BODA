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
    buildRsvpSubmission,
    createRsvpPreviewData,
    normalizeRsvpData,
    resolveInvitationId,
} from "../components/rsvp.js";

import {
    INTERACTION_TRIGGERS,
    InteractionEngine,
} from "../interaction/index.js";

import {
    resolveDataBoundText,
} from "../data_bindings/index.js";

export class UniversalRenderer {
    constructor(options = {}) {
        this.options = {
            editable: false,
            device: "desktop",
            onNodeClick: null,
            onInteractionResult: null,
            onInteractionError: null,
            assetResolver: null,
            rsvpProvider: null,
            invitationContext: {},
            eventContext: {},
            onRsvpResult: null,
            onRsvpError: null,
            interactionEngine:
                new InteractionEngine(),
            ...options,
        };

        this.document = null;
        this.root = null;
        this.nodeMap = new Map();
        this.countdownTimer = null;
    }

    mount(root, document) {
        if (!(root instanceof Element)) {
            throw new TypeError(
                "root debe ser un elemento HTML válido."
            );
        }

        const normalized =
            normalizeDocument(document);
        const validation =
            validateDocument(normalized);

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
                ...normalized.canvases,
                ...normalized.nodes,
            ].map((node) => [node.id, node])
        );

        this.render();
        this.startCountdownTicker();

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

        this.stopCountdownTicker();
        this.root.replaceChildren();
        this.root.classList.add("r3-page");
        this.root.dataset.r3Device =
            this.options.device;
        this.root.dataset.r3Editable =
            this.options.editable ? "1" : "0";

        const fragment =
            this.root.ownerDocument
                .createDocumentFragment();

        const canvass = [
            ...this.document.canvases,
        ].sort((a, b) => a.order - b.order);

        for (const canvas of canvass) {
            if (!canvas.visible) continue;

            fragment.append(
                this.renderNode(canvas)
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

        if (node.type === NODE_TYPES.CANVAS) {
            element.dataset.r3CanvasId =
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

        const structuralCanvas =
            node.type === NODE_TYPES.CANVAS;

        element.style.setProperty(
            "--r3-width",
            structuralCanvas
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
                structuralCanvas ? "px" : "%"
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
                this.applyCountdownBindingMetadata(element, node);
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

            case NODE_TYPES.COUNTDOWN:
                this.applyCountdownPresentation(
                    element,
                    node
                );
                break;

            case NODE_TYPES.RSVP:
                this.applyRsvpContent(element, node);
                break;

            case NODE_TYPES.SEPARATOR:
                element.setAttribute("aria-hidden", "true");
                break;

            default:
                break;
        }
    }

    applyCountdownPresentation(
        element,
        node
    ) {
        const presentation = String(
            node.content?.presentation
            || "CARDS"
        ).toUpperCase();

        element.dataset.r3CountdownPresentation =
            presentation === "PLAIN"
                ? "PLAIN"
                : "CARDS";

        element.dataset.r3CountdownShowLabels =
            node.content?.showLabels === false
                ? "0"
                : "1";
    }

    applyRsvpContent(element, node) {
        const content = node.content || {};
        const invitationContext =
            this.options.invitationContext
            || {};
        const runtimePreview =
            Array.isArray(invitationContext.guests)
            && invitationContext.guests.length
                ? invitationContext
                : createRsvpPreviewData(
                    content.preview || {}
                );
        const preview = normalizeRsvpData(
            runtimePreview
        );
        const invitationId = resolveInvitationId(
            invitationContext
        );
        const provider = this.options.rsvpProvider;

        element.replaceChildren();
        element.classList.add("r3-rsvp");
        element.style.setProperty("--r3-rsvp-accent", node.style?.accentColor || "#526043");

        const renderForm = (rawData) => {
            const data = normalizeRsvpData({
                ...rawData,
                invitationId: rawData?.invitationId || invitationId,
            });
            const configuredDensity = String(
                content.density || "AUTO"
            ).toUpperCase();
            element.dataset.r3RsvpDensity =
                configuredDensity === "AUTO"
                    ? (data.guests.length >= 4
                        ? "COMPACT"
                        : "COMFORTABLE")
                    : configuredDensity;
            element.replaceChildren();

            const title = element.ownerDocument.createElement("h3");
            title.className = "r3-rsvp__title";
            title.textContent = content.title || "Confirma tu asistencia";

            const description = element.ownerDocument.createElement("p");
            description.className = "r3-rsvp__description";
            description.textContent =
                content.description
                || "Cada persona puede confirmar su asistencia de forma individual.";

            element.append(title, description);

            if (content.showGroupName !== false) {
                const group = element.ownerDocument.createElement("strong");
                group.className = "r3-rsvp__group";
                group.textContent = data.groupName;
                element.append(group);
            }

            if (!data.guests.length) {
                const empty = element.ownerDocument.createElement("p");
                empty.className = "r3-rsvp__status";
                empty.textContent = "Esta invitación todavía no tiene personas asignadas.";
                element.append(empty);
                return;
            }

            const list = element.ownerDocument.createElement("div");
            list.className = "r3-rsvp__people";

            for (const guest of data.guests) {
                const form = element.ownerDocument.createElement("form");
                form.className = "r3-rsvp__person";
                form.dataset.rsvpGuestId = guest.id;

                const personHeader = element.ownerDocument.createElement("div");
                personHeader.className = "r3-rsvp__person-header";

                const identity = element.ownerDocument.createElement("div");
                identity.className = "r3-rsvp__identity";

                const name = element.ownerDocument.createElement("strong");
                name.className = "r3-rsvp__person-name";
                name.textContent = guest.name;
                identity.append(name);

                const badges = element.ownerDocument.createElement("div");
                badges.className = "r3-rsvp__badges";

                if (content.showPersonType !== false && guest.personTypeLabel) {
                    const typeBadge = element.ownerDocument.createElement("span");
                    typeBadge.className = "r3-rsvp__badge";
                    typeBadge.dataset.kind = "person";
                    typeBadge.textContent = guest.personTypeLabel;
                    badges.append(typeBadge);
                }

                if (content.showMenu !== false && guest.menuLabel) {
                    const menuBadge = element.ownerDocument.createElement("span");
                    menuBadge.className = "r3-rsvp__badge";
                    menuBadge.dataset.kind = "menu";
                    menuBadge.textContent = guest.menuLabel;
                    badges.append(menuBadge);
                }

                if (badges.childElementCount) {
                    identity.append(badges);
                }

                const state = element.ownerDocument.createElement("span");
                state.className = "r3-rsvp__person-state";
                state.textContent = guest.attending === true
                    ? "Confirmado"
                    : guest.attending === false
                        ? "No asiste"
                        : "Pendiente";
                state.dataset.state = guest.status;

                personHeader.append(identity, state);

                const question = element.ownerDocument.createElement("span");
                question.className = "r3-rsvp__question";
                question.textContent = "¿Asistirás?";

                const choices = element.ownerDocument.createElement("div");
                choices.className = "r3-rsvp__choices";
                const inputName = `rsvp-attending-${node.id}-${guest.id}`;

                for (const [value, label] of [
                    ["yes", content.acceptLabel || "Sí asistiré"],
                    ["no", content.declineLabel || "No asistiré"],
                ]) {
                    const choice = element.ownerDocument.createElement("label");
                    choice.className = "r3-rsvp__choice";

                    const input = element.ownerDocument.createElement("input");
                    input.type = "radio";
                    input.name = inputName;
                    input.value = value;
                    input.checked = value === "yes"
                        ? guest.attending === true
                        : guest.attending === false;

                    const text = element.ownerDocument.createElement("span");
                    text.textContent = label;
                    choice.append(input, text);
                    choices.append(choice);
                }

                const submit = element.ownerDocument.createElement("button");
                submit.className = "r3-rsvp__submit";
                submit.type = "submit";
                submit.textContent = content.submitLabel || "Guardar respuesta";

                const status = element.ownerDocument.createElement("div");
                status.className = "r3-rsvp__status";
                status.setAttribute("aria-live", "polite");

                form.append(personHeader, question, choices, submit, status);

                form.addEventListener("submit", async (event) => {
                    event.preventDefault();
                    if (this.options.editable) return;

                    const selected = form.querySelector(`input[name="${inputName}"]:checked`);
                    if (!selected) {
                        status.textContent = "Selecciona una respuesta.";
                        return;
                    }

                    const payload = buildRsvpSubmission({
                        guestId: guest.id,
                        attending: selected.value,
                    }, data);

                    if (!provider?.submit) {
                        status.textContent = "Vista previa: la respuesta se guardará al publicar.";
                        this.options.onRsvpResult?.({ node, payload, preview: true });
                        return;
                    }

                    submit.disabled = true;
                    status.textContent = "Guardando…";
                    try {
                        const result = await provider.submit(
                            payload,
                            { node, document: this.document, invitationId }
                        );
                        const nextData = result?.data || data;
                        renderForm(nextData);
                        this.options.onRsvpResult?.({ node, payload, result });
                    } catch (error) {
                        status.textContent = "No se pudo guardar la respuesta.";
                        this.options.onRsvpError?.(error, { node, payload });
                        submit.disabled = false;
                    }
                });

                list.append(form);
            }

            element.append(list);
        };

        renderForm(preview);

        if (!this.options.editable && provider?.load && invitationId) {
            Promise.resolve(provider.load(invitationId, { node, document: this.document }))
                .then((data) => renderForm(data || preview))
                .catch((error) => this.options.onRsvpError?.(error, { node, invitationId }));
        }
    }

    applyVideoContent(element, node) {
        const content = node.content || {};
        const sourceValue =
            content.sourceType === "library"
            && content.assetId
                ? this.resolveAssetUrl(node)
                : (
                    content.source
                    || content.src
                    || ""
                );

        const source = normalizeVideoSource(
            sourceValue,
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


    applyCountdownBindingMetadata(element, node) {
        const binding = node.content?.binding;

        if (binding?.source !== "COUNTDOWN") {
            return;
        }

        const countdown = this.findAncestorByType(
            node,
            NODE_TYPES.COUNTDOWN
        );

        if (!countdown) {
            return;
        }

        element.dataset.r3CountdownId = countdown.id;
        element.dataset.r3CountdownUnit = String(binding.unit || "");
        element.dataset.r3CountdownRole = String(binding.role || "value");
    }

    startCountdownTicker() {
        this.stopCountdownTicker();
        this.updateCountdownBindings();

        const hasActiveCountdown = [...this.nodeMap.values()].some((node) => {
            if (node.type !== NODE_TYPES.COUNTDOWN || !node.visible) return false;
            return Number.isFinite(this.resolveCountdownTarget(node));
        });

        if (!hasActiveCountdown) {
            return;
        }

        this.countdownTimer = setInterval(() => {
            this.updateCountdownBindings();
        }, 1000);
    }

    stopCountdownTicker() {
        if (this.countdownTimer !== null) {
            clearInterval(this.countdownTimer);
            this.countdownTimer = null;
        }
    }

    destroy() {
        this.stopCountdownTicker();
        this.root = null;
        this.document = null;
        this.nodeMap = new Map();
    }

    updateCountdownBindings(now = Date.now()) {
        if (!this.root) return;

        const countdowns = [...this.nodeMap.values()]
            .filter((node) => node.type === NODE_TYPES.COUNTDOWN && node.visible);

        for (const countdown of countdowns) {
            const target = this.resolveCountdownTarget(countdown);
            if (!Number.isFinite(target)) continue;

            const values = this.calculateCountdownValues(target, now);
            countdown.content = countdown.content || {};
            countdown.content.values = values;

            const boundElements = this.root.querySelectorAll("[data-r3-countdown-id]");
            for (const element of boundElements) {
                if (element.dataset.r3CountdownId !== countdown.id) continue;
                if (element.dataset.r3CountdownRole !== "value") continue;

                const unitIndex = {
                    days: 0,
                    hours: 1,
                    minutes: 2,
                    seconds: 3,
                }[element.dataset.r3CountdownUnit];

                if (unitIndex === undefined) continue;
                element.textContent = String(values[unitIndex]);
            }
        }
    }

    resolveCountdownTarget(node) {
        const content = node?.content || {};
        const configuredSource = String(
            content.targetSource || ""
        ).toUpperCase();

        // Preserve old documents: before R.6 a countdown only knew targetDate.
        // If that value exists and no source was stored, it remains CUSTOM.
        const source = configuredSource
            || (content.targetDate ? "CUSTOM" : "RECEPTION");

        const eventContext =
            this.options.eventContext || {};

        const valueBySource = {
            EVENT: eventContext.eventDate,
            CEREMONY: eventContext.ceremonyDate,
            RECEPTION: eventContext.receptionDate,
            CUSTOM: content.targetDate,
        };

        return this.resolveCountdownTimestamp(
            valueBySource[source]
        );
    }

    resolveCountdownTimestamp(value) {
        if (value === null || value === undefined || value === "") {
            return Number.NaN;
        }

        if (typeof value === "number") {
            return Number.isFinite(value) ? value : Number.NaN;
        }

        const parsed = new Date(String(value)).getTime();
        return Number.isFinite(parsed) ? parsed : Number.NaN;
    }

    calculateCountdownValues(targetTimestamp, nowTimestamp = Date.now()) {
        let remaining = Math.max(0, targetTimestamp - nowTimestamp);
        const day = 24 * 60 * 60 * 1000;
        const hour = 60 * 60 * 1000;
        const minute = 60 * 1000;
        const second = 1000;

        const days = Math.floor(remaining / day);
        remaining %= day;
        const hours = Math.floor(remaining / hour);
        remaining %= hour;
        const minutes = Math.floor(remaining / minute);
        remaining %= minute;
        const seconds = Math.floor(remaining / second);

        return [days, hours, minutes, seconds];
    }

    resolveTextContent(node) {
        const binding = node.content?.binding;
        const fallback =
            node.content?.text || "";

        if (
            binding?.source
            && binding.source !== "COUNTDOWN"
        ) {
            return resolveDataBoundText(
                binding,
                {
                    eventContext:
                        this.options.eventContext
                        || {},
                    invitationContext:
                        this.options.invitationContext
                        || {},
                    fallback,
                }
            );
        }

        if (binding?.source !== "COUNTDOWN") {
            return fallback;
        }

        const countdown = this.findAncestorByType(
            node,
            NODE_TYPES.COUNTDOWN
        );

        if (!countdown) {
            return fallback;
        }

        const unitIndex = {
            days: 0,
            hours: 1,
            minutes: 2,
            seconds: 3,
        }[binding.unit];

        if (unitIndex === undefined) {
            return fallback;
        }

        if (binding.role === "label") {
            return String(
                node.content?.text
                ?? ""
            );
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