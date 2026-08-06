export class CanvasWorkspaceController {
    #app;
    #workspace;
    #selectedCanvasId = null;

    constructor({ app, workspace }) {
        if (!app?.getDocument || !app?.updateDocument) {
            throw new TypeError("CanvasWorkspaceController requiere BuilderApp.");
        }
        this.#app = app;
        this.#workspace = workspace || null;
    }

    get selectedCanvasId() {
        return this.#selectedCanvasId;
    }

    initialize() {
        const documentValue = this.#app.getDocument();
        const canvases = Array.isArray(documentValue.canvases)
            ? documentValue.canvases
            : [];

        const preferred = this.#workspace?.value?.selectedCanvasId;
        const selected = canvases.find((item) => item.id === preferred)
            || canvases.find((item) => item.visible !== false)
            || canvases[0]
            || null;

        this.select(selected?.id || null);
        return this;
    }

    list() {
        const documentValue = this.#app.getDocument();
        return [...(documentValue.canvases || [])]
            .sort((a, b) => Number(a.order || 0) - Number(b.order || 0));
    }

    getSelected() {
        return this.list().find((item) => item.id === this.#selectedCanvasId) || null;
    }

    select(canvasId) {
        const exists = canvasId && this.list().some((item) => item.id === canvasId);
        this.#selectedCanvasId = exists ? canvasId : null;

        this.#workspace?.update((state) => {
            state.selectedCanvasId = this.#selectedCanvasId;
        });

        return this.getSelected();
    }

    create(options = {}) {
        const current = this.list();
        const id = String(options.id || createId("canvas"));
        const canvas = {
            id,
            name: String(options.name || `Lienzo ${current.length + 1}`),
            type: String(options.type || "PERSONALIZADA").toUpperCase(),
            visible: options.visible !== false,
            locked: false,
            order: nextOrder(current),
            height: finiteNumber(options.height, 700),
            background: {
                color: String(options.backgroundColor || "#ffffff"),
                opacity: 1,
            },
            metadata: {
                createdByEngine: true,
            },
            nodes: [],
        };

        this.#app.updateDocument((document) => {
            document.canvases = Array.isArray(document.canvases)
                ? document.canvases
                : [];
            document.canvases.push(canvas);
        }, {
            label: `Crear ${canvas.name}`,
            source: "canvas-workspace",
        });

        this.select(canvas.id);
        return canvas;
    }

    duplicate(canvasId = this.#selectedCanvasId) {
        const source = this.list().find((item) => item.id === canvasId);
        if (!source) throw new Error("Lienzo no encontrado.");

        const clone = deepClone(source);
        clone.id = createId("canvas");
        clone.name = `${source.name || "Lienzo"} copia`;
        clone.order = nextOrder(this.list());
        clone.metadata = {
            ...(clone.metadata || {}),
            duplicatedFrom: source.id,
        };
        regenerateNodeIds(clone.nodes || []);

        this.#app.updateDocument((document) => {
            document.canvases.push(clone);
        }, {
            label: `Duplicar ${source.name || "lienzo"}`,
            source: "canvas-workspace",
        });

        this.select(clone.id);
        return clone;
    }

    remove(canvasId = this.#selectedCanvasId) {
        const canvases = this.list();
        if (canvases.length <= 1) {
            throw new Error("El documento debe conservar al menos un lienzo.");
        }

        const target = canvases.find((item) => item.id === canvasId);
        if (!target) throw new Error("Lienzo no encontrado.");
        if (target.locked) throw new Error("El lienzo está bloqueado.");

        this.#app.updateDocument((document) => {
            document.canvases = document.canvases
                .filter((item) => item.id !== canvasId);
            normalizeOrders(document.canvases);
        }, {
            label: `Eliminar ${target.name || "lienzo"}`,
            source: "canvas-workspace",
        });

        const remaining = this.list();
        this.select(remaining[0]?.id || null);
        return true;
    }

    move(canvasId, direction) {
        const canvases = this.list();
        const index = canvases.findIndex((item) => item.id === canvasId);
        if (index < 0) throw new Error("Lienzo no encontrado.");

        const offset = direction === "up" ? -1 : direction === "down" ? 1 : 0;
        const targetIndex = index + offset;
        if (!offset || targetIndex < 0 || targetIndex >= canvases.length) {
            return false;
        }

        [canvases[index], canvases[targetIndex]] = [
            canvases[targetIndex],
            canvases[index],
        ];
        normalizeOrders(canvases);

        this.#app.updateDocument((document) => {
            document.canvases = canvases;
        }, {
            label: "Reordenar lienzos",
            source: "canvas-workspace",
        });

        return true;
    }

    rename(canvasId, name) {
        const clean = String(name || "").trim();
        if (!clean) throw new Error("El nombre del lienzo es obligatorio.");

        this.#app.updateDocument((document) => {
            const canvas = document.canvases.find((item) => item.id === canvasId);
            if (!canvas) throw new Error("Lienzo no encontrado.");
            canvas.name = clean.slice(0, 120);
        }, {
            label: "Renombrar lienzo",
            source: "canvas-workspace",
            mergeKey: `canvas:${canvasId}:name`,
        });

        return this.list().find((item) => item.id === canvasId);
    }

    toggleVisibility(canvasId) {
        this.#app.updateDocument((document) => {
            const canvas = document.canvases.find((item) => item.id === canvasId);
            if (!canvas) throw new Error("Lienzo no encontrado.");
            canvas.visible = canvas.visible === false;
        }, {
            label: "Cambiar visibilidad del lienzo",
            source: "canvas-workspace",
        });
    }
}

function nextOrder(canvases) {
    return canvases.reduce(
        (max, item) => Math.max(max, Number(item.order || 0)),
        0,
    ) + 10;
}

function normalizeOrders(canvases) {
    canvases.forEach((item, index) => {
        item.order = (index + 1) * 10;
    });
}

function regenerateNodeIds(nodes) {
    for (const node of nodes) {
        node.id = createId(String(node.type || "node").toLowerCase());
        regenerateNodeIds(Array.isArray(node.children) ? node.children : []);
    }
}

function createId(prefix) {
    const suffix = globalThis.crypto?.randomUUID
        ? globalThis.crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    return `${prefix}-${suffix}`;
}

function finiteNumber(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}

function deepClone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
