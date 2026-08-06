
export function screenDeltaToLogical({ dx = 0, dy = 0 }, { zoom = 1, scale = 1 } = {}) {
    const factor = Math.max((Number(zoom) || 1) * (Number(scale) || 1), 0.0001);
    return { dx: Number(dx) / factor, dy: Number(dy) / factor };
}

export function logicalToPercent(transform, parentSize) {
    const width = Math.max(Number(parentSize?.width) || 1, 1);
    const height = Math.max(Number(parentSize?.height) || 1, 1);
    return {
        ...transform,
        x: Number(transform.x) / width * 100,
        y: Number(transform.y) / height * 100,
        width: Number(transform.width) / width * 100,
        height: Number(transform.height) / height * 100,
    };
}

export function percentToLogical(transform, parentSize) {
    const width = Math.max(Number(parentSize?.width) || 1, 1);
    const height = Math.max(Number(parentSize?.height) || 1, 1);
    return {
        ...transform,
        x: Number(transform.x) / 100 * width,
        y: Number(transform.y) / 100 * height,
        width: Number(transform.width) / 100 * width,
        height: Number(transform.height) / 100 * height,
    };
}
