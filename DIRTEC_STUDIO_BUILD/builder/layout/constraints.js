export const CONSTRAINTS = Object.freeze({
    LEFT: "LEFT",
    CENTER_X: "CENTER_X",
    RIGHT: "RIGHT",
    SCALE_X: "SCALE_X",
    TOP: "TOP",
    CENTER_Y: "CENTER_Y",
    BOTTOM: "BOTTOM",
    SCALE_Y: "SCALE_Y",
});

export function normalizeConstraints(value = {}) {
    return {
        horizontal: value.horizontal || CONSTRAINTS.CENTER_X,
        vertical: value.vertical || CONSTRAINTS.CENTER_Y,
        keepAspect: Boolean(value.keepAspect),
    };
}

export function applyConstraints({ node, previousParent, nextParent }) {
    const constraints = normalizeConstraints(node.constraints);
    const patch = {};
    const previousWidth = number(previousParent?.width, 100);
    const previousHeight = number(previousParent?.height, 100);
    const nextWidth = number(nextParent?.width, previousWidth);
    const nextHeight = number(nextParent?.height, previousHeight);

    if (constraints.horizontal === CONSTRAINTS.LEFT) {
        patch.x = number(node.width, 20) / 2;
    } else if (constraints.horizontal === CONSTRAINTS.RIGHT) {
        patch.x = 100 - number(node.width, 20) / 2;
    } else if (constraints.horizontal === CONSTRAINTS.CENTER_X) {
        patch.x = 50;
    } else if (constraints.horizontal === CONSTRAINTS.SCALE_X) {
        const ratio = nextWidth / Math.max(previousWidth, 1);
        patch.x = number(node.x, 50) * ratio;
        patch.width = number(node.width, 20) * ratio;
    }

    if (constraints.vertical === CONSTRAINTS.TOP) {
        patch.y = number(node.height, 20) / 2;
    } else if (constraints.vertical === CONSTRAINTS.BOTTOM) {
        patch.y = 100 - number(node.height, 20) / 2;
    } else if (constraints.vertical === CONSTRAINTS.CENTER_Y) {
        patch.y = 50;
    } else if (constraints.vertical === CONSTRAINTS.SCALE_Y) {
        const ratio = nextHeight / Math.max(previousHeight, 1);
        patch.y = number(node.y, 50) * ratio;
        patch.height = number(node.height, 20) * ratio;
    }

    if (constraints.keepAspect && patch.width && !patch.height) {
        patch.height = patch.width * (
            number(node.height, 20) / Math.max(number(node.width, 20), 1)
        );
    }

    return patch;
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}