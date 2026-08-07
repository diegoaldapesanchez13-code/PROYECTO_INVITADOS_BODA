import { COORDINATE_SPACES } from "./constants.js";

export class CoordinateSpaceResolver {
    resolve(node, context = {}) {
        const requested = String(
            node?.layout?.coordinateSpace
            || node?.coordinateSpace
            || COORDINATE_SPACES.PARENT
        ).toUpperCase();

        if (requested === COORDINATE_SPACES.CANVAS) {
            return {
                kind: COORDINATE_SPACES.CANVAS,
                id: context.canvasId || null,
                width: positive(context.canvasWidth, 1),
                height: positive(context.canvasHeight, 1),
                zoom: positive(context.zoom, 1),
            };
        }

        return {
            kind: COORDINATE_SPACES.PARENT,
            id: context.parentId || context.canvasId || null,
            width: positive(context.parentWidth ?? context.canvasWidth, 1),
            height: positive(context.parentHeight ?? context.canvasHeight, 1),
            zoom: positive(context.zoom, 1),
        };
    }

    pointerDeltaToPercent(delta, space) {
        const zoom = positive(space?.zoom, 1);
        return {
            x: (Number(delta?.x || 0) / zoom / positive(space?.width, 1)) * 100,
            y: (Number(delta?.y || 0) / zoom / positive(space?.height, 1)) * 100,
        };
    }
}

function positive(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}
