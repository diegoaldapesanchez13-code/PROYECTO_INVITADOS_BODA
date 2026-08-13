import {
    NODE_TYPES,
} from "../core/index.js";

import {
    TRANSFORM_KINDS,
    coordinateParentFor,
    getTransformPolicy,
} from "./transform_policy.js";

const HANDLE_DIRECTIONS = Object.freeze([
    "nw",
    "n",
    "ne",
    "e",
    "se",
    "s",
    "sw",
    "w",
]);

export class CanvasSelectionEngine {
    constructor(options) {
        const {
            state,
            renderer,
            viewport,
            zoomLayer,
            surface,
            overlayLayer,
            onSelectionChange = null,
            onInteractionState = null,
        } = options || {};

        if (!state || !renderer) {
            throw new Error(
                "CanvasSelectionEngine requiere state y renderer."
            );
        }

        for (
            const [name, element]
            of Object.entries({
                viewport,
                zoomLayer,
                surface,
                overlayLayer,
            })
        ) {
            if (!(element instanceof Element)) {
                throw new Error(
                    `${name} debe ser un elemento HTML.`
                );
            }
        }

        this.state = state;
        this.renderer = renderer;
        this.viewport = viewport;
        this.zoomLayer = zoomLayer;
        this.surface = surface;
        this.overlayLayer = overlayLayer;
        this.onSelectionChange = onSelectionChange;
        this.onInteractionState = onInteractionState;

        this.zoom = 1;
        this.selectedNodeId = null;
        this.selectedElement = null;
        this.interaction = null;

        this.overlay = this.#createOverlay();
        this.overlayLayer.append(this.overlay);

        this.#bind();
        this.setZoom(1);
    }

    destroy() {
        this.overlay.remove();

        this.viewport.removeEventListener(
            "pointerdown",
            this.boundViewportPointerDown,
            true
        );

        window.removeEventListener(
            "resize",
            this.boundRefresh
        );

        this.viewport.removeEventListener(
            "scroll",
            this.boundRefresh
        );
    }

    select(nodeId) {
        if (!nodeId) {
            this.clearSelection();
            return null;
        }

        const node =
            this.state.getNode(nodeId);

        if (!node) {
            this.clearSelection();
            return null;
        }

        if (this.selectedNodeId === node.id) {
            this.#resolveSelectedElement();
            this.refreshOverlay();
            return node;
        }

        this.selectedNodeId = node.id;
        this.state.selectNode(node.id);
        this.#resolveSelectedElement();
        this.refreshOverlay();

        this.onSelectionChange?.(
            node,
            this.selectedElement
        );

        return node;
    }

    clearSelection() {
        this.selectedNodeId = null;
        this.selectedElement = null;
        this.overlay.hidden = true;
        this.state.selectNode(null);
        this.onSelectionChange?.(null, null);
    }

    setZoom(value) {
        const next = clamp(
            Number(value) || 1,
            0.25,
            2
        );

        this.zoom = next;

        this.zoomLayer.style.setProperty(
            "--r3-canvas-zoom",
            String(next)
        );

        requestAnimationFrame(
            () => this.refreshOverlay()
        );

        return next;
    }

    fitToViewport({
        horizontalPadding = 48,
        verticalPadding = 48,
    } = {}) {
        const rect =
            this.viewport.getBoundingClientRect();

        const surfaceWidth =
            this.surface.scrollWidth
            || this.surface.offsetWidth
            || 1;

        const surfaceHeight =
            this.surface.scrollHeight
            || this.surface.offsetHeight
            || 1;

        return this.setZoom(
            Math.min(
                (
                    rect.width
                    - horizontalPadding
                ) / surfaceWidth,
                (
                    rect.height
                    - verticalPadding
                ) / surfaceHeight,
                1
            )
        );
    }

    refreshAfterRender() {
        this.#resolveSelectedElement();
        this.refreshOverlay();
    }

    refreshOverlay() {
        if (
            !this.selectedNodeId
            || !this.selectedElement
            || !this.selectedElement.isConnected
        ) {
            this.overlay.hidden = true;
            return;
        }

        const node =
            this.state.getNode(
                this.selectedNodeId
            );

        if (!node) {
            this.clearSelection();
            return;
        }

        const elementRect =
            this.selectedElement
                .getBoundingClientRect();

        const layerRect =
            this.overlayLayer
                .getBoundingClientRect();

        this.overlay.hidden = false;

        this.overlay.style.left =
            `${
                (
                    elementRect.left
                    - layerRect.left
                ) / this.zoom
            }px`;

        this.overlay.style.top =
            `${
                (
                    elementRect.top
                    - layerRect.top
                ) / this.zoom
            }px`;

        this.overlay.style.width =
            `${Math.max(
                elementRect.width
                / this.zoom,
                1
            )}px`;

        this.overlay.style.height =
            `${Math.max(
                elementRect.height
                / this.zoom,
                1
            )}px`;

        const policy =
            getTransformPolicy(node);

        this.overlay.dataset.transformKind =
            policy.kind;

        this.overlay.classList.toggle(
            "is-transformable",
            policy.movable
        );

        this.overlay.classList.toggle(
            "is-background-pan",
            policy.kind
            === TRANSFORM_KINDS.BACKGROUND_PAN
        );

        const label =
            this.overlay.querySelector(
                "[data-r3-selection-label]"
            );

        label.textContent =
            policy.kind
            === TRANSFORM_KINDS.BACKGROUND_PAN
                ? `${node.name} · arrastra para encuadrar`
                : `${node.type} · ${node.name}`;

        this.overlay.querySelectorAll(
            "[data-r3-resize-handle]"
        ).forEach((handle) => {
            handle.hidden =
                !policy.resizable;
        });
    }

    #bind() {
        this.boundViewportPointerDown =
            (event) => {
                const overlayTarget =
                    event.target.closest(
                        "[data-r3-selection-overlay]"
                    );

                if (overlayTarget) {
                    return;
                }

                const nodeElement =
                    event.target.closest(
                        "[data-r3-node-id]"
                    );

                if (
                    !nodeElement
                    || !this.surface.contains(
                        nodeElement
                    )
                ) {
                    this.clearSelection();
                    return;
                }

                const nodeId =
                    nodeElement.dataset.r3NodeId;

                const node =
                    this.select(nodeId);

                const policy =
                    getTransformPolicy(node);

                if (
                    event.button === 0
                    && policy.movable
                ) {
                    this.#startInteraction(
                        event,
                        policy.kind,
                        null
                    );
                }
            };

        this.viewport.addEventListener(
            "pointerdown",
            this.boundViewportPointerDown,
            true
        );

        this.boundRefresh =
            () => this.refreshOverlay();

        window.addEventListener(
            "resize",
            this.boundRefresh
        );

        this.viewport.addEventListener(
            "scroll",
            this.boundRefresh
        );

        this.overlay.addEventListener(
            "pointerdown",
            (event) => {
                const node =
                    this.state.getNode(
                        this.selectedNodeId
                    );

                const policy =
                    getTransformPolicy(node);

                if (!policy.movable) {
                    return;
                }

                const handle =
                    event.target.closest(
                        "[data-r3-resize-handle]"
                    );

                event.preventDefault();
                event.stopPropagation();

                this.#startInteraction(
                    event,
                    handle
                        ? "RESIZE"
                        : policy.kind,
                    handle?.dataset
                        .r3ResizeHandle
                        || null
                );
            }
        );
    }

    #createOverlay() {
        const overlay =
            document.createElement("div");

        overlay.className =
            "r3-selection-overlay";

        overlay.dataset.r3SelectionOverlay =
            "1";

        overlay.hidden = true;

        const label =
            document.createElement("div");

        label.className =
            "r3-selection-overlay__label";

        label.dataset.r3SelectionLabel =
            "1";

        overlay.append(label);

        for (
            const direction
            of HANDLE_DIRECTIONS
        ) {
            const handle =
                document.createElement("button");

            handle.type = "button";

            handle.className =
                "r3-selection-handle "
                + `r3-selection-handle--${direction}`;

            handle.dataset.r3ResizeHandle =
                direction;

            handle.setAttribute(
                "aria-label",
                `Redimensionar ${direction}`
            );

            overlay.append(handle);
        }

        return overlay;
    }

    #resolveSelectedElement() {
        if (!this.selectedNodeId) {
            this.selectedElement = null;
            return;
        }

        this.selectedElement =
            this.surface.querySelector(
                `[data-r3-node-id="${cssEscape(
                    this.selectedNodeId
                )}"]`
            );
    }

    #startInteraction(
        event,
        mode,
        handle
    ) {
        const node =
            this.state.getNode(
                this.selectedNodeId
            );

        const element =
            this.selectedElement;

        if (!node || !element) {
            return;
        }

        const parentElement =
            coordinateParentFor({
                node,
                element,
                surface: this.surface,
            });

        if (!parentElement) {
            return;
        }

        const parentRect =
            parentElement
                .getBoundingClientRect();

        const parentWidth =
            Math.max(
                parentElement.clientWidth,
                parentElement.offsetWidth,
                parentRect.width
                    / Math.max(this.zoom, .01),
                1
            );

        const parentHeight =
            Math.max(
                parentElement.clientHeight,
                parentElement.offsetHeight,
                parentRect.height
                    / Math.max(this.zoom, .01),
                1
            );

        const elementRect =
            element.getBoundingClientRect();

        const elementCenterX =
            elementRect.left
            + elementRect.width / 2;

        const elementCenterY =
            elementRect.top
            + elementRect.height / 2;

        this.interaction = {
            mode,
            handle,
            pointerId: event.pointerId,
            pointerType: event.pointerType,
            startClientX: event.clientX,
            startClientY: event.clientY,
            pointerOffsetX:
                event.clientX
                - elementCenterX,
            pointerOffsetY:
                event.clientY
                - elementCenterY,
            startNode:
                structuredCloneSafe(node),
            parentElement,
            parentWidth,
            parentHeight,
            elementRect,
            activated: false,
            previewPatch: null,
            threshold:
                event.pointerType === "touch"
                    ? 10
                    : 4,
        };

        this.overlay.setPointerCapture?.(
            event.pointerId
        );

        const move =
            (moveEvent) =>
                this.#updateInteraction(
                    moveEvent
                );

        const finish =
            () => {
                cleanup();
                this.#finishInteraction();
            };

        const cancel =
            () => {
                cleanup();
                this.#cancelInteraction();
            };

        const cleanup =
            () => {
                this.overlay.removeEventListener(
                    "pointermove",
                    move
                );

                this.overlay.removeEventListener(
                    "pointerup",
                    finish
                );

                this.overlay.removeEventListener(
                    "pointercancel",
                    cancel
                );
            };

        this.overlay.addEventListener(
            "pointermove",
            move
        );

        this.overlay.addEventListener(
            "pointerup",
            finish
        );

        this.overlay.addEventListener(
            "pointercancel",
            cancel
        );

        this.onInteractionState?.({
            active: true,
            mode,
            node,
        });
    }

    #updateInteraction(event) {
        const interaction =
            this.interaction;

        if (
            !interaction
            || event.pointerId
                !== interaction.pointerId
        ) {
            return;
        }

        const deltaX =
            (
                event.clientX
                - interaction.startClientX
            ) / Math.max(this.zoom, .01);

        const deltaY =
            (
                event.clientY
                - interaction.startClientY
            ) / Math.max(this.zoom, .01);

        if (!interaction.activated) {
            if (
                Math.hypot(deltaX, deltaY)
                < interaction.threshold
            ) {
                return;
            }

            interaction.activated = true;
        }

        if (
            interaction.mode
            === TRANSFORM_KINDS.BACKGROUND_PAN
        ) {
            this.#previewBackgroundPan(
                interaction,
                deltaX,
                deltaY
            );
            return;
        }

        if (
            interaction.mode === "RESIZE"
        ) {
            this.#previewGeometry(
                this.#resizePatch(
                    interaction,
                    deltaX,
                    deltaY
                )
            );
            return;
        }

        this.#previewGeometry(
            this.#movePatch(
                interaction,
                event
            )
        );
    }

    #movePatch(
        interaction,
        event
    ) {
        /*
         * El movimiento se calcula directamente desde la posición
         * actual del puntero dentro del rectángulo visual del padre.
         *
         * Esto elimina dependencias del zoom, del alto CSS auto y de
         * acumulaciones por delta. X e Y usan exactamente la misma
         * fórmula.
         */
        const parentRect =
            interaction.parentElement
                .getBoundingClientRect();

        const visualWidth =
            Math.max(
                parentRect.width,
                1
            );

        const visualHeight =
            Math.max(
                parentRect.height,
                1
            );

        const centerClientX =
            event.clientX
            - interaction.pointerOffsetX;

        const centerClientY =
            event.clientY
            - interaction.pointerOffsetY;

        const x =
            (
                centerClientX
                - parentRect.left
            ) / visualWidth * 100;

        const y =
            (
                centerClientY
                - parentRect.top
            ) / visualHeight * 100;

        return {
            x: round(
                clamp(x, -100, 200),
                2
            ),
            y: round(
                clamp(y, -100, 200),
                2
            ),
        };
    }

    #resizePatch(
        interaction,
        deltaX,
        deltaY
    ) {
        const node =
            interaction.startNode;

        const handle =
            interaction.handle;

        const startWidth =
            numericDimension(
                node.width,
                (
                    interaction.elementRect.width
                    / Math.max(
                        interaction.parentWidth,
                        1
                    )
                ) * 100
            );

        const startHeight =
            numericDimension(
                node.height,
                (
                    interaction.elementRect.height
                    / Math.max(
                        interaction.parentHeight,
                        1
                    )
                ) * 100
            );

        const parentRect =
            interaction.parentElement
                .getBoundingClientRect();

        const deltaWidth =
            (
                deltaX
                * Math.max(this.zoom, .01)
            )
            / Math.max(
                parentRect.width,
                1
            )
            * 100;

        const deltaHeight =
            (
                deltaY
                * Math.max(this.zoom, .01)
            )
            / Math.max(
                parentRect.height,
                1
            )
            * 100;

        let width = startWidth;
        let height = startHeight;
        let x = Number(node.x ?? 50);
        let y = Number(node.y ?? 50);

        if (handle.includes("e")) {
            width += deltaWidth;
            x += deltaWidth / 2;
        }

        if (handle.includes("w")) {
            width -= deltaWidth;
            x += deltaWidth / 2;
        }

        if (handle.includes("s")) {
            height += deltaHeight;
            y += deltaHeight / 2;
        }

        if (handle.includes("n")) {
            height -= deltaHeight;
            y += deltaHeight / 2;
        }

        return {
            x: round(
                clamp(x, -100, 200),
                2
            ),
            y: round(
                clamp(y, -100, 200),
                2
            ),
            width: round(
                clamp(width, 4, 180),
                2
            ),
            height: round(
                clamp(height, 2, 180),
                2
            ),
        };
    }

    #previewGeometry(patch) {
        if (!this.selectedElement) {
            return;
        }

        const current =
            this.state.getNode(
                this.selectedNodeId
            );

        const merged = {
            ...current,
            ...patch,
        };

        this.selectedElement.style.setProperty(
            "--r3-x",
            `${Number(merged.x ?? 50)}%`
        );

        this.selectedElement.style.setProperty(
            "--r3-y",
            `${Number(merged.y ?? 50)}%`
        );

        this.selectedElement.style.setProperty(
            "--r3-width",
            dimensionToCss(
                merged.width,
                "%"
            )
        );

        this.selectedElement.style.setProperty(
            "--r3-height",
            dimensionToCss(
                merged.height,
                "%"
            )
        );

        this.interaction.previewPatch = {
            ...(this.interaction.previewPatch || {}),
            ...patch,
        };

        this.refreshOverlay();
    }

    #previewBackgroundPan(
        interaction,
        deltaX,
        deltaY
    ) {
        const node =
            interaction.startNode;

        const startStyle = {
            ...(node.style || {}),
        };

        const positionX = round(
            clamp(
                Number(
                    startStyle.positionX
                    ?? 50
                )
                + (
                    deltaX
                    / interaction.parentWidth
                ) * 100,
                0,
                100
            ),
            2
        );

        const positionY = round(
            clamp(
                Number(
                    startStyle.positionY
                    ?? 50
                )
                + (
                    deltaY
                    / interaction.parentHeight
                ) * 100,
                0,
                100
            ),
            2
        );

        const style = {
            ...startStyle,
            positionX,
            positionY,
        };

        this.selectedElement.style
            .backgroundPosition =
                `${positionX}% ${positionY}%`;

        this.interaction.previewPatch = {
            style,
        };

        this.refreshOverlay();
    }

    #finishInteraction() {
        const interaction =
            this.interaction;

        this.interaction = null;

        if (
            !interaction
            || !interaction.activated
            || !interaction.previewPatch
        ) {
            this.refreshOverlay();

            this.onInteractionState?.({
                active: false,
                committed: false,
            });

            return;
        }

        this.state.updateNode(
            this.selectedNodeId,
            interaction.previewPatch
        );

        this.renderer.update(
            this.state.document
        );

        this.#resolveSelectedElement();
        this.refreshOverlay();

        this.onInteractionState?.({
            active: false,
            committed: true,
            patch:
                interaction.previewPatch,
        });
    }

    #cancelInteraction() {
        this.interaction = null;

        this.renderer.update(
            this.state.document
        );

        this.#resolveSelectedElement();
        this.refreshOverlay();

        this.onInteractionState?.({
            active: false,
            cancelled: true,
        });
    }
}

function numericDimension(
    value,
    fallback
) {
    if (value === "auto") {
        return fallback;
    }

    const parsed = Number(value);

    return Number.isFinite(parsed)
        ? parsed
        : fallback;
}

function dimensionToCss(
    value,
    numericUnit
) {
    if (value === "auto") {
        return "auto";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? `${number}${numericUnit}`
        : "auto";
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}

function cssEscape(value) {
    if (
        globalThis.CSS
        && typeof CSS.escape === "function"
    ) {
        return CSS.escape(String(value));
    }

    return String(value).replace(
        /["\\]/g,
        "\\$&"
    );
}

function round(value, decimals) {
    const factor =
        10 ** decimals;

    return Math.round(value * factor)
        / factor;
}

function clamp(value, min, max) {
    return Math.min(
        Math.max(value, min),
        max
    );
}
