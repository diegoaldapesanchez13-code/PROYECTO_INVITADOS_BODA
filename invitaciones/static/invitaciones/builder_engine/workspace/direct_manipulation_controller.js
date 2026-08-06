import {
    dragTransform,
    resizeTransform,
    rotationFromPoints,
    resolveResponsiveStyle,
    writeResponsiveStyle,
} from "./transform_math.js";

export class DirectManipulationController {
    #nodeWorkspace;
    #workspace;
    #session = null;

    constructor({ nodeWorkspace, workspace }) {
        if (!nodeWorkspace?.getSelected || !nodeWorkspace?.update) {
            throw new TypeError("DirectManipulationController requiere NodeWorkspaceController.");
        }
        this.#nodeWorkspace = nodeWorkspace;
        this.#workspace = workspace || null;
    }

    get active() { return Boolean(this.#session); }

    get device() {
        return normalizeDevice(this.#workspace?.value?.previewDevice);
    }

    setDevice(device) {
        const normalized = normalizeDevice(device);
        this.#workspace?.update((state) => {
            state.previewDevice = normalized;
        });
        return normalized;
    }

    begin(mode, pointer, geometry = {}) {
        const node = this.#nodeWorkspace.getSelected();
        if (!node) throw new Error("No hay un elemento seleccionado.");
        if (node.locked) throw new Error("El elemento está bloqueado.");

        const device = this.device;
        this.#session = {
            mode,
            device,
            nodeId: node.id,
            pointer: point(pointer),
            initial: resolveResponsiveStyle(node.style || {}, device),
            bounds: {
                width: positive(geometry.canvasWidth, 1),
                height: positive(geometry.canvasHeight, 1),
            },
            center: point(geometry.center || pointer),
            handle: geometry.handle || "se",
        };
        return this.preview(pointer);
    }

    preview(pointer, options = {}) {
        if (!this.#session) return null;
        const current = point(pointer);
        const delta = {
            x: current.x - this.#session.pointer.x,
            y: current.y - this.#session.pointer.y,
        };

        if (this.#session.mode === "drag") {
            return dragTransform(this.#session.initial, delta, this.#session.bounds, {
                snap: options.altKey ? 0 : 0.25,
            });
        }
        if (this.#session.mode === "resize") {
            return resizeTransform(
                this.#session.initial,
                delta,
                this.#session.bounds,
                this.#session.handle,
                { minWidth: 2, maxWidth: 300 },
            );
        }
        if (this.#session.mode === "rotate") {
            return {
                ...this.#session.initial,
                rotation: rotationFromPoints(
                    this.#session.center,
                    this.#session.pointer,
                    current,
                    this.#session.initial.rotation,
                    { shiftKey: options.shiftKey, snap: 15 },
                ),
            };
        }
        return { ...this.#session.initial };
    }

    commit(transform) {
        if (!this.#session) return false;
        const node = this.#nodeWorkspace.getSelected();
        if (!node || node.id !== this.#session.nodeId) {
            this.cancel();
            return false;
        }

        const patch = {};
        for (const key of ["x", "y", "width", "scale", "rotation", "opacity", "zIndex"]) {
            if (transform[key] !== undefined) patch[key] = transform[key];
        }

        const nextStyle = writeResponsiveStyle(
            node.style || {},
            patch,
            this.#session.device,
        );

        this.#nodeWorkspace.update("style", nextStyle, {
            label: labelForMode(this.#session.mode),
            mergeKey: null,
        });

        this.#session = null;
        return true;
    }

    cancel() { this.#session = null; }
}

function normalizeDevice(value) {
    const key = String(value || "").toLowerCase();
    if (key.includes("tablet")) return "tablet";
    if (key.includes("desktop")) return "desktop";
    return "mobile";
}

function point(value = {}) {
    return {
        x: Number(value.x ?? value.clientX ?? 0),
        y: Number(value.y ?? value.clientY ?? 0),
    };
}

function positive(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function labelForMode(mode) {
    return {
        drag: "Mover elemento",
        resize: "Redimensionar elemento",
        rotate: "Rotar elemento",
    }[mode] || "Transformar elemento";
}
