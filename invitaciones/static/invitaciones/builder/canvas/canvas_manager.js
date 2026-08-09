import {
    NODE_TYPES,
} from "../core/index.js?v=f4-native-v4-freeze";

export const MOBILE_CANVAS_WIDTH = 390;
export const DEFAULT_CANVAS_HEIGHT = 844;
export const MIN_CANVAS_HEIGHT = 240;
export const MAX_CANVAS_HEIGHT = 6000;

export function createBlankCanvasConfig(options = {}) {
    const height = clampNumber(
        options.height ?? DEFAULT_CANVAS_HEIGHT,
        MIN_CANVAS_HEIGHT,
        MAX_CANVAS_HEIGHT,
    );

    return {
        name: String(options.name || "Nuevo lienzo"),
        width: 100,
        height,
        minHeight: 0,
        maxHeight: 0,
        visible: options.visible !== false,
        locked: false,
        style: {
            paddingX: 0,
            paddingY: 0,
            overflow: "hidden",
            direction: "column",
            align: "stretch",
            justify: "start",
            gap: 0,
            sizingX: "fixed",
            sizingY: "fixed",
        },
    };
}

export class CanvasManager {
    constructor(options = {}) {
        const {
            root,
            state,
            canvas,
            renderer,
            onDocumentChange = null,
            onStatus = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "CanvasManager root debe ser un elemento HTML.",
            );
        }

        if (!state || !canvas || !renderer) {
            throw new Error(
                "CanvasManager requiere state, canvas y renderer.",
            );
        }

        this.root = root;
        this.state = state;
        this.canvas = canvas;
        this.renderer = renderer;
        this.onDocumentChange = onDocumentChange;
        this.onStatus = onStatus;

        this.unsubscribe = this.state.subscribe((event) => {
            if (
                event.type === "selection:change"
                || event.type === "selection:clear"
            ) {
                this.#syncSelection();
                return;
            }

            this.render();
        });

        this.render();
    }

    destroy() {
        this.unsubscribe?.();
        this.root.replaceChildren();
    }

    createCanvas() {
        const count = canvasesOf(this.state.document).length;
        const node = this.state.createNode(
            NODE_TYPES.CANVAS,
            createBlankCanvasConfig({
                name: `Lienzo ${count + 1}`,
            }),
        );

        this.#changed(`Creado ${node.name}`);
        this.canvas.select(node.id);
        return node;
    }

    duplicateCanvas(nodeId) {
        const source = this.state.getNode(nodeId);
        if (!source || source.type !== NODE_TYPES.CANVAS) {
            return null;
        }

        const clone = this.state.duplicateNode(nodeId);
        this.#changed(`Duplicado ${source.name}`);
        this.canvas.select(clone.id);
        return clone;
    }

    deleteCanvas(nodeId) {
        const canvass = canvasesOf(this.state.document);
        if (canvass.length <= 1) {
            this.onStatus?.(
                "El documento debe conservar al menos un lienzo.",
            );
            return false;
        }

        const node = this.state.getNode(nodeId);
        if (!node || node.type !== NODE_TYPES.CANVAS) {
            return false;
        }

        if (node.locked) {
            this.onStatus?.(
                "Desbloquea el lienzo antes de eliminarlo.",
            );
            return false;
        }

        const confirmed = globalThis.confirm
            ? globalThis.confirm(`¿Eliminar "${node.name}" y todas sus capas?`)
            : true;

        if (!confirmed) {
            return false;
        }

        const previousIndex = canvass.findIndex(
            (canvas) => canvas.id === node.id,
        );

        this.state.deleteNode(node.id);

        const remaining = canvasesOf(this.state.document)
            .sort((a, b) => a.order - b.order);
        const next = remaining[
            Math.min(previousIndex, remaining.length - 1)
        ] || remaining[0];

        this.#changed(`Eliminado ${node.name}`);

        if (next) {
            this.canvas.select(next.id);
        } else {
            this.canvas.clearSelection();
        }

        return true;
    }

    moveCanvas(nodeId, direction) {
        const canvass = canvasesOf(this.state.document)
            .sort((a, b) => a.order - b.order);
        const index = canvass.findIndex(
            (canvas) => canvas.id === nodeId,
        );

        if (index < 0) {
            return null;
        }

        const nextIndex = direction === "UP"
            ? index - 1
            : index + 1;

        if (nextIndex < 0 || nextIndex >= canvass.length) {
            return this.state.getNode(nodeId);
        }

        const node = this.state.reorderNode(nodeId, nextIndex);
        this.#changed(`Orden actualizado: ${node.name}`);
        this.canvas.select(node.id);
        return node;
    }

    render() {
        this.root.replaceChildren();
        this.root.classList.add("r3-canvas-manager");

        this.root.append(
            this.#renderHeader(),
            this.#renderList(),
        );

        this.#syncSelection();
    }

    #renderHeader() {
        const header = document.createElement("header");
        header.className = "r3-canvas-manager__header";

        const text = document.createElement("div");
        text.innerHTML = `
            <strong>Lienzos</strong>
            <small>${MOBILE_CANVAS_WIDTH}px de ancho · altura libre</small>
        `;

        const add = document.createElement("button");
        add.type = "button";
        add.textContent = "+ Lienzo";
        add.addEventListener("click", () => this.createCanvas());

        header.append(text, add);
        return header;
    }

    #renderList() {
        const list = document.createElement("div");
        list.className = "r3-canvas-manager__list";

        const canvass = canvasesOf(this.state.document)
            .sort((a, b) => a.order - b.order);

        for (const [index, canvas] of canvass.entries()) {
            list.append(
                this.#renderItem(canvas, index, canvass.length),
            );
        }

        return list;
    }

    #renderItem(node, index, total) {
        const item = document.createElement("article");
        item.className = "r3-canvas-manager__item";
        item.dataset.r3CanvasId = node.id;

        const select = document.createElement("button");
        select.type = "button";
        select.className = "r3-canvas-manager__select";
        select.innerHTML = `
            <span class="r3-canvas-manager__number">${index + 1}</span>
            <span>
                <strong>${escapeHtml(node.name)}</strong>
                <small>${displayHeight(node)} px</small>
            </span>
        `;
        select.addEventListener("click", () => {
            this.canvas.select(node.id);
            this.#scrollCanvasIntoView(node.id);
        });

        const controls = document.createElement("div");
        controls.className = "r3-canvas-manager__controls";

        controls.append(
            actionButton("↑", "Subir lienzo", index === 0, () => {
                this.moveCanvas(node.id, "UP");
            }),
            actionButton("↓", "Bajar lienzo", index === total - 1, () => {
                this.moveCanvas(node.id, "DOWN");
            }),
            actionButton("⧉", "Duplicar lienzo", false, () => {
                this.duplicateCanvas(node.id);
            }),
            actionButton("×", "Eliminar lienzo", total <= 1, () => {
                this.deleteCanvas(node.id);
            }),
        );

        item.append(select, controls);
        return item;
    }

    #scrollCanvasIntoView(nodeId) {
        const element = this.renderer.root?.querySelector(
            `[data-r3-canvas-id="${cssEscape(nodeId)}"]`,
        );

        element?.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });
    }

    #syncSelection() {
        const selectedCanvasId = this.state.selection.canvasId;

        this.root.querySelectorAll("[data-r3-canvas-id]")
            .forEach((item) => {
                item.classList.toggle(
                    "is-selected",
                    item.dataset.r3CanvasId === selectedCanvasId,
                );
            });
    }

    #changed(message) {
        this.renderer.update(this.state.document);
        this.canvas.refreshAfterRender();
        this.onDocumentChange?.(this.state.document);
        this.onStatus?.(message);
        this.render();
    }
}

function actionButton(label, title, disabled, handler) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.title = title;
    button.disabled = disabled;
    button.addEventListener("click", handler);
    return button;
}

function displayHeight(node) {
    if (node.height !== "auto") {
        const height = Number(node.height);
        if (Number.isFinite(height) && height > 0) {
            return Math.round(height);
        }
    }

    return Math.max(
        Math.round(Number(node.minHeight || DEFAULT_CANVAS_HEIGHT)),
        MIN_CANVAS_HEIGHT,
    );
}

function clampNumber(value, min, max) {
    const number = Number(value);
    const safe = Number.isFinite(number) ? number : min;
    return Math.min(Math.max(safe, min), max);
}

function cssEscape(value) {
    if (globalThis.CSS?.escape) {
        return globalThis.CSS.escape(String(value));
    }

    return String(value).replace(/["\\]/g, "\\$&");
}

function canvasesOf(documentState) {
    return Array.isArray(documentState?.canvases)
        ? [...documentState.canvases]
        : [];
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
