
export class CanvasHeightSession {
    constructor({ height, pointerY, zoom = 1, minHeight = 320, maxHeight = 12000 }) {
        this.startHeight = Number(height);
        this.currentHeight = this.startHeight;
        this.pointerY = Number(pointerY);
        this.zoom = Math.max(Number(zoom) || 1, .01);
        this.minHeight = Number(minHeight);
        this.maxHeight = Number(maxHeight);
    }

    update(pointerY) {
        const delta = (Number(pointerY) - this.pointerY) / this.zoom;
        this.currentHeight = clamp(this.startHeight + delta, this.minHeight, this.maxHeight);
        return this.currentHeight;
    }

    commit() {
        return Object.freeze({ before: this.startHeight, after: this.currentHeight });
    }

    cancel() {
        this.currentHeight = this.startHeight;
        return this.currentHeight;
    }
}

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
