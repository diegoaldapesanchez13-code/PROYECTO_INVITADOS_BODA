
const HANDLES = Object.freeze(["n","ne","e","se","s","sw","w","nw"]);

export const TRANSFORM_HANDLES = HANDLES;

export class TransformSession {
    constructor({ nodeId, transform, pointer, operation = "MOVE", handle = null, zoom = 1 }) {
        if (!nodeId) throw new TypeError("nodeId es obligatorio.");
        this.nodeId = nodeId;
        this.operation = String(operation).toUpperCase();
        this.handle = handle;
        this.zoom = Math.max(Number(zoom) || 1, 0.01);
        this.start = normalizeTransform(transform);
        this.current = { ...this.start };
        this.pointerStart = point(pointer);
        this.pointerCurrent = { ...this.pointerStart };
        this.cancelled = false;
        this.committed = false;
    }

    update(pointer, options = {}) {
        if (this.cancelled || this.committed) return { ...this.current };
        this.pointerCurrent = point(pointer);
        const dx = (this.pointerCurrent.x - this.pointerStart.x) / this.zoom;
        const dy = (this.pointerCurrent.y - this.pointerStart.y) / this.zoom;

        if (this.operation === "MOVE") {
            this.current = {
                ...this.start,
                x: this.start.x + dx,
                y: this.start.y + dy,
            };
        } else if (this.operation === "RESIZE") {
            this.current = resize(this.start, dx, dy, this.handle, options);
        } else if (this.operation === "ROTATE") {
            this.current = rotate(this.start, this.pointerStart, this.pointerCurrent, options.center);
        }
        return { ...this.current };
    }

    commit() {
        if (this.cancelled) return null;
        this.committed = true;
        return Object.freeze({
            nodeId: this.nodeId,
            before: { ...this.start },
            after: { ...this.current },
            operation: this.operation,
            handle: this.handle,
        });
    }

    cancel() {
        this.cancelled = true;
        this.current = { ...this.start };
        return { ...this.current };
    }
}

function resize(start, dx, dy, handle, options = {}) {
    if (!HANDLES.includes(handle)) throw new TypeError(`Handle inválido: ${handle}`);
    const minWidth = Number(options.minWidth ?? 1);
    const minHeight = Number(options.minHeight ?? 1);
    let { x, y, width, height } = start;

    if (handle.includes("e")) width += dx;
    if (handle.includes("s")) height += dy;
    if (handle.includes("w")) { width -= dx; x += dx; }
    if (handle.includes("n")) { height -= dy; y += dy; }

    if (width < minWidth) {
        if (handle.includes("w")) x -= minWidth - width;
        width = minWidth;
    }
    if (height < minHeight) {
        if (handle.includes("n")) y -= minHeight - height;
        height = minHeight;
    }

    if (options.lockAspectRatio) {
        const ratio = Number(options.aspectRatio || start.width / Math.max(start.height, .0001));
        if (["e","w"].includes(handle)) height = width / ratio;
        else if (["n","s"].includes(handle)) width = height * ratio;
        else {
            const byWidth = width / ratio;
            const byHeight = height * ratio;
            if (Math.abs(byWidth - start.height) >= Math.abs(byHeight - start.width)) {
                height = byWidth;
            } else {
                width = byHeight;
            }
        }
    }

    return { ...start, x, y, width, height };
}

function rotate(start, pointerStart, pointerCurrent, center = null) {
    const c = center || { x: start.x + start.width / 2, y: start.y + start.height / 2 };
    const a0 = Math.atan2(pointerStart.y - c.y, pointerStart.x - c.x);
    const a1 = Math.atan2(pointerCurrent.y - c.y, pointerCurrent.x - c.x);
    return { ...start, rotation: start.rotation + (a1 - a0) * 180 / Math.PI };
}

function normalizeTransform(value = {}) {
    return {
        x: Number(value.x || 0),
        y: Number(value.y || 0),
        width: Number(value.width || 0),
        height: Number(value.height || 0),
        rotation: Number(value.rotation || 0),
        opacity: Number(value.opacity ?? 1),
        originX: Number(value.originX ?? .5),
        originY: Number(value.originY ?? .5),
    };
}

function point(value = {}) {
    return { x: Number(value.x || 0), y: Number(value.y || 0) };
}
