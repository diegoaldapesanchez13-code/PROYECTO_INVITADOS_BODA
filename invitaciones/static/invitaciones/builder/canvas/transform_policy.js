import {
    LAYOUT_MODES,
    NODE_TYPES,
} from "../core/index.js";

export const TRANSFORM_KINDS = Object.freeze({
    NONE: "NONE",
    GEOMETRY: "GEOMETRY",
    BACKGROUND_PAN: "BACKGROUND_PAN",
});

export function getTransformPolicy(node) {
    if (!node || node.locked) {
        return {
            kind: TRANSFORM_KINDS.NONE,
            movable: false,
            resizable: false,
            reason: "locked-or-missing",
        };
    }

    /*
     * Una SECTION es un bloque estructural de la página.
     * Permanece en FLOW; se ajusta desde Alto mínimo,
     * padding y contenido, no arrastrándola como una capa.
     */
    if (node.type === NODE_TYPES.CANVAS) {
        return {
            kind: TRANSFORM_KINDS.NONE,
            movable: false,
            resizable: false,
            reason: "canvas-is-structural",
        };
    }

    /*
     * Un BACKGROUND ocupa todo su contenedor.
     * Arrastrarlo significa mover la imagen dentro del marco,
     * no mover el rectángulo del fondo.
     */
    if (node.type === NODE_TYPES.BACKGROUND) {
        return {
            kind: TRANSFORM_KINDS.BACKGROUND_PAN,
            movable: true,
            resizable: false,
            reason: "background-pan",
        };
    }

    const geometryLayout = [
        LAYOUT_MODES.ABSOLUTE,
        LAYOUT_MODES.LAYER,
    ].includes(node.layoutMode);

    return {
        kind: geometryLayout
            ? TRANSFORM_KINDS.GEOMETRY
            : TRANSFORM_KINDS.NONE,
        movable: geometryLayout,
        resizable: geometryLayout,
        reason: geometryLayout
            ? "free-geometry"
            : "flow-managed",
    };
}

export function effectiveLayoutMode(node) {
    if (!node) {
        return LAYOUT_MODES.FLOW;
    }

    if (node.type === NODE_TYPES.CANVAS) {
        return LAYOUT_MODES.FLOW;
    }

    if (node.type === NODE_TYPES.BACKGROUND) {
        return LAYOUT_MODES.LAYER;
    }

    return node.layoutMode;
}

export function coordinateParentFor({
    node,
    element,
    surface,
}) {
    if (!node || !element || !surface) {
        return null;
    }

    if (node.type === NODE_TYPES.CANVAS) {
        return surface;
    }

    if (
        node.coordinateSpace === "CANVAS"
    ) {
        const canvas =
            element.closest(
                "[data-r3-canvas-id]"
            );

        if (
            canvas
            && canvas !== element
        ) {
            return canvas;
        }

        return surface;
    }

    return element.parentElement
        || surface;
}