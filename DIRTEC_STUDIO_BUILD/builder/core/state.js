import {
    NODE_TYPES,
    createEmptyDocument,
    createNode,
    normalizeDocument,
    normalizeNode,
    serializeDocument,
    validateDocument,
} from "./schema.js?v=phase-f3-canvas-contract";

import {
    canonicalizeDocumentV4,
} from "./runtime_v4.js?v=phase-f3-canvas-contract";

export class BuilderState {
    #document;
    #listeners = new Set();
    #selection = {
        nodeId: null,
        canvasId: null,
    };
    #history = [];
    #future = [];
    #transactionDepth = 0;
    #pendingHistory = false;
    #maxHistory;

    constructor(initialDocument = null, options = {}) {
        this.#maxHistory = Number(options.maxHistory || 100);
        this.#document = normalizeDocument(
            canonicalizeDocumentV4(
                initialDocument || createEmptyDocument()
            )
        );
        this.#assertValid();
    }

    get document() {
        return structuredCloneSafe(this.#document);
    }

    get selection() {
        return { ...this.#selection };
    }

    get canUndo() {
        return this.#history.length > 0;
    }

    get canRedo() {
        return this.#future.length > 0;
    }

    subscribe(listener) {
        if (typeof listener !== "function") {
            throw new TypeError("listener debe ser una función.");
        }

        this.#listeners.add(listener);

        return () => {
            this.#listeners.delete(listener);
        };
    }

    selectNode(nodeId) {
        if (nodeId === null) {
            this.#selection = {
                nodeId: null,
                canvasId: null,
            };
            this.#emit("selection:clear");
            return null;
        }

        const node = this.getNode(nodeId);

        if (!node) {
            throw new Error(`Nodo no encontrado: ${nodeId}`);
        }

        this.#selection = {
            nodeId: node.id,
            canvasId:
                node.type === NODE_TYPES.CANVAS
                    ? node.id
                    : node.canvasId,
        };

        this.#emit("selection:change", {
            selection: this.selection,
        });

        return structuredCloneSafe(node);
    }

    getNode(nodeId) {
        return this.#findNode(nodeId);
    }

    getChildren(parentId) {
        return this.#allNodes()
            .filter((node) => node.parentId === parentId)
            .sort((a, b) => a.order - b.order)
            .map(structuredCloneSafe);
    }

    getCanvasNodes(canvasId) {
        return this.#allNodes()
            .filter((node) => node.canvasId === canvasId)
            .sort((a, b) => a.order - b.order)
            .map(structuredCloneSafe);
    }

    createNode(type, overrides = {}) {
        return this.transaction("node:create", () => {
            const node = createNode(type, overrides);

            if (node.type === NODE_TYPES.CANVAS) {
                node.canvasId = node.id;
                node.parentId = null;
                node.order = this.#document.canvases.length;
                this.#document.canvases.push(node);
            } else {
                this.#validateParentAssignment(node);
                node.order = this.#nextOrder(node.parentId);
                this.#document.nodes.push(node);
                this.#attachToParent(node);
            }

            this.#touch();
            this.selectNode(node.id);

            return structuredCloneSafe(node);
        });
    }

    updateNode(nodeId, patch, options = {}) {
        return this.transaction("node:update", () => {
            const current = this.#findNode(nodeId);

            if (!current) {
                throw new Error(`Nodo no encontrado: ${nodeId}`);
            }

            if (
                current.locked
                && options.ignoreLock !== true
            ) {
                throw new Error(
                    `El nodo está bloqueado: ${nodeId}`
                );
            }

            const previousParentId = current.parentId;
            const next = normalizeNode({
                ...current,
                ...structuredCloneSafe(patch),
                id: current.id,
                type: current.type,
            });

            if (next.type !== NODE_TYPES.CANVAS) {
                this.#validateParentAssignment(next);

                if (previousParentId !== next.parentId) {
                    this.#detachFromParent(current);
                    this.#replaceNode(next);
                    this.#attachToParent(next);
                } else {
                    this.#replaceNode(next);
                }
            } else {
                next.canvasId = next.id;
                next.parentId = null;
                this.#replaceNode(next);
            }

            this.#touch();

            return structuredCloneSafe(next);
        });
    }

    deleteNode(nodeId, options = {}) {
        return this.transaction("node:delete", () => {
            const node = this.#findNode(nodeId);

            if (!node) {
                throw new Error(`Nodo no encontrado: ${nodeId}`);
            }

            if (
                node.locked
                && options.ignoreLock !== true
            ) {
                throw new Error(
                    `El nodo está bloqueado: ${nodeId}`
                );
            }

            const descendantIds = this.#descendantIds(nodeId);
            const deleteIds = new Set([
                nodeId,
                ...descendantIds,
            ]);

            this.#document.canvases =
                this.#document.canvases.filter(
                    (item) => !deleteIds.has(item.id)
                );

            this.#document.nodes =
                this.#document.nodes.filter(
                    (item) => !deleteIds.has(item.id)
                );

            for (const item of this.#allNodes()) {
                item.children = item.children.filter(
                    (childId) => !deleteIds.has(childId)
                );
            }

            this.#reindexAll();

            if (deleteIds.has(this.#selection.nodeId)) {
                this.#selection = {
                    nodeId: null,
                    canvasId: null,
                };
            }

            this.#touch();

            return [...deleteIds];
        });
    }

    moveNode(nodeId, newParentId, index = null) {
        return this.transaction("node:move", () => {
            const node = this.#findNode(nodeId);

            if (!node) {
                throw new Error(`Nodo no encontrado: ${nodeId}`);
            }

            if (node.type === NODE_TYPES.CANVAS) {
                throw new Error(
                    "Un CANVAS no puede tener parent."
                );
            }

            const previousParentId = node.parentId;
            const next = normalizeNode({
                ...node,
                parentId: newParentId,
            });

            this.#validateParentAssignment(next);

            this.#detachFromParent(node);
            this.#replaceNode(next);
            this.#attachToParent(next, index);

            if (previousParentId !== newParentId) {
                this.#propagateCanvasId(
                    next.id,
                    next.canvasId
                );
            }

            this.#reindexSiblings(previousParentId);
            this.#reindexSiblings(newParentId);
            this.#touch();

            return structuredCloneSafe(
                this.#findNode(nodeId)
            );
        });
    }

    reorderNode(nodeId, index) {
        return this.transaction("node:reorder", () => {
            const node = this.#findNode(nodeId);

            if (!node) {
                throw new Error(`Nodo no encontrado: ${nodeId}`);
            }

            if (node.type === NODE_TYPES.CANVAS) {
                const list = this.#document.canvases;
                reorderList(list, node.id, index);
                this.#reindexCanvases();
            } else {
                const siblings = this.#siblings(node.parentId);
                reorderList(siblings, node.id, index);
                this.#applySiblingOrder(
                    node.parentId,
                    siblings
                );
            }

            this.#touch();

            return structuredCloneSafe(
                this.#findNode(nodeId)
            );
        });
    }

    duplicateNode(nodeId, options = {}) {
        return this.transaction("node:duplicate", () => {
            const source = this.#findNode(nodeId);

            if (!source) {
                throw new Error(`Nodo no encontrado: ${nodeId}`);
            }

            const idMap = new Map();
            const subtree = [
                source,
                ...this.#descendants(nodeId),
            ];

            for (const node of subtree) {
                idMap.set(
                    node.id,
                    createNode(
                        node.type,
                        {}
                    ).id
                );
            }

            const clones = subtree.map((node) => {
                const clone = normalizeNode({
                    ...structuredCloneSafe(node),
                    id: idMap.get(node.id),
                    name:
                        node.id === source.id
                            ? `${node.name} copia`
                            : node.name,
                    parentId:
                        node.id === source.id
                            ? (
                                options.parentId
                                ?? node.parentId
                            )
                            : idMap.get(node.parentId),
                    children: node.children.map(
                        (childId) => idMap.get(childId)
                    ),
                });

                if (
                    source.type === NODE_TYPES.CANVAS
                ) {
                    clone.canvasId = idMap.get(
                        node.canvasId
                    );
                } else {
                    clone.canvasId = source.canvasId;
                }

                return clone;
            });

            const rootClone = clones.find(
                (node) => node.id === idMap.get(source.id)
            );

            if (
                rootClone.type === NODE_TYPES.CANVAS
            ) {
                rootClone.parentId = null;
                rootClone.canvasId = rootClone.id;
                this.#document.canvases.push(rootClone);

                this.#document.nodes.push(
                    ...clones.filter(
                        (node) =>
                            node.type !== NODE_TYPES.CANVAS
                    )
                );
            } else {
                this.#document.nodes.push(...clones);
                this.#attachToParent(rootClone);
            }

            this.#reindexAll();
            this.#touch();
            this.selectNode(rootClone.id);

            return structuredCloneSafe(rootClone);
        });
    }

    transaction(label, callback) {
        const outermost = this.#transactionDepth === 0;

        if (outermost) {
            this.#history.push(
                this.#snapshot(label)
            );
            this.#future = [];

            if (this.#history.length > this.#maxHistory) {
                this.#history.shift();
            }
        }

        this.#transactionDepth += 1;

        try {
            const result = callback();
            this.#transactionDepth -= 1;

            if (outermost) {
                this.#assertValid();
                this.#emit(label, { result });
            }

            return result;
        } catch (error) {
            this.#transactionDepth -= 1;

            if (outermost) {
                const snapshot = this.#history.pop();
                this.#restoreSnapshot(snapshot);
            }

            throw error;
        }
    }

    undo() {
        const snapshot = this.#history.pop();

        if (!snapshot) return false;

        this.#future.push(
            this.#snapshot("redo")
        );
        this.#restoreSnapshot(snapshot);
        this.#emit("history:undo");

        return true;
    }

    redo() {
        const snapshot = this.#future.pop();

        if (!snapshot) return false;

        this.#history.push(
            this.#snapshot("undo")
        );
        this.#restoreSnapshot(snapshot);
        this.#emit("history:redo");

        return true;
    }

    replaceDocument(document, options = {}) {
        const normalized = normalizeDocument(document);
        const validation = validateDocument(normalized);

        if (!validation.valid) {
            throw new Error(
                validation.errors.join("\n")
            );
        }

        if (options.recordHistory !== false) {
            this.#history.push(
                this.#snapshot("document:replace")
            );
        }

        this.#document = normalized;
        this.#selection = {
            nodeId: null,
            canvasId: null,
        };
        this.#future = [];
        this.#emit("document:replace");
    }

    serialize(spacing = 2) {
        return serializeDocument(
            this.#document,
            spacing
        );
    }

    validate() {
        return validateDocument(this.#document);
    }

    #findNode(nodeId) {
        return this.#allNodes().find(
            (node) => node.id === String(nodeId)
        ) || null;
    }

    #replaceNode(nextNode) {
        const canvasIndex =
            this.#document.canvases.findIndex(
                (node) => node.id === nextNode.id
            );

        if (canvasIndex >= 0) {
            this.#document.canvases[canvasIndex] = nextNode;
            return;
        }

        const nodeIndex =
            this.#document.nodes.findIndex(
                (node) => node.id === nextNode.id
            );

        if (nodeIndex < 0) {
            throw new Error(
                `No se pudo reemplazar ${nextNode.id}`
            );
        }

        this.#document.nodes[nodeIndex] = nextNode;
    }

    #validateParentAssignment(node) {
        if (!node.parentId) {
            throw new Error(
                `${node.type} requiere parentId.`
            );
        }

        const parent = this.#findNode(node.parentId);

        if (!parent) {
            throw new Error(
                `Parent inexistente: ${node.parentId}`
            );
        }

        if (
            node.id
            && this.#descendantIds(node.id)
                .includes(parent.id)
        ) {
            throw new Error(
                "No se puede mover un nodo dentro de su descendiente."
            );
        }

        node.canvasId =
            parent.type === NODE_TYPES.CANVAS
                ? parent.id
                : parent.canvasId;

        if (!node.canvasId) {
            throw new Error(
                "No se pudo resolver canvasId."
            );
        }
    }

    #attachToParent(node, index = null) {
        const parent = this.#findNode(node.parentId);

        if (!parent) {
            throw new Error(
                `Parent inexistente: ${node.parentId}`
            );
        }

        const children = parent.children.filter(
            (childId) => childId !== node.id
        );

        const targetIndex = normalizeIndex(
            index,
            children.length
        );

        children.splice(targetIndex, 0, node.id);
        parent.children = children;
        this.#replaceNode(parent);
        this.#reindexSiblings(parent.id);
    }

    #detachFromParent(node) {
        if (!node.parentId) return;

        const parent = this.#findNode(node.parentId);

        if (!parent) return;

        parent.children = parent.children.filter(
            (childId) => childId !== node.id
        );

        this.#replaceNode(parent);
    }

    #descendantIds(nodeId) {
        return this.#descendants(nodeId)
            .map((node) => node.id);
    }

    #descendants(nodeId) {
        const result = [];
        const node = this.#findNode(nodeId);

        if (!node) return result;

        for (const childId of node.children) {
            const child = this.#findNode(childId);

            if (!child) continue;

            result.push(child);
            result.push(
                ...this.#descendants(child.id)
            );
        }

        return result;
    }

    #siblings(parentId) {
        if (!parentId) return [];

        const parent = this.#findNode(parentId);

        if (!parent) return [];

        return parent.children
            .map((id) => this.#findNode(id))
            .filter(Boolean)
            .sort((a, b) => a.order - b.order);
    }

    #nextOrder(parentId) {
        const siblings = this.#siblings(parentId);
        return siblings.length;
    }

    #applySiblingOrder(parentId, siblings) {
        const parent = this.#findNode(parentId);

        if (!parent) return;

        parent.children = siblings.map(
            (node, index) => {
                node.order = index;
                this.#replaceNode(node);
                return node.id;
            }
        );

        this.#replaceNode(parent);
    }

    #reindexSiblings(parentId) {
        if (!parentId) return;

        const siblings = this.#siblings(parentId);
        this.#applySiblingOrder(parentId, siblings);
    }

    #reindexCanvases() {
        this.#document.canvases.forEach(
            (canvas, index) => {
                canvas.order = index;
            }
        );
    }

    #reindexAll() {
        this.#reindexCanvases();

        for (const node of this.#allNodes()) {
            if (node.children.length) {
                this.#reindexSiblings(node.id);
            }
        }
    }

    #propagateCanvasId(nodeId, canvasId) {
        const node = this.#findNode(nodeId);

        if (!node) return;

        node.canvasId = canvasId;
        this.#replaceNode(node);

        for (const childId of node.children) {
            this.#propagateCanvasId(
                childId,
                canvasId
            );
        }
    }

    #allNodes() {
        return [
            ...this.#document.canvases,
            ...this.#document.nodes,
        ];
    }

    #snapshot(label) {
        return {
            label,
            document: structuredCloneSafe(
                this.#document
            ),
            selection: { ...this.#selection },
        };
    }

    #restoreSnapshot(snapshot) {
        if (!snapshot) return;

        this.#document = structuredCloneSafe(
            snapshot.document
        );
        this.#selection = {
            ...snapshot.selection,
        };
    }

    #touch() {
        this.#document.meta.updatedAt =
            new Date().toISOString();
    }

    #assertValid() {
        const validation = validateDocument(
            this.#document
        );

        if (!validation.valid) {
            throw new Error(
                validation.errors.join("\n")
            );
        }
    }

    #emit(type, detail = {}) {
        const event = {
            type,
            detail,
            document: this.document,
            selection: this.selection,
        };

        for (const listener of this.#listeners) {
            listener(event);
        }
    }
}

function reorderList(list, nodeId, index) {
    const currentIndex = list.findIndex(
        (node) => node.id === nodeId
    );

    if (currentIndex < 0) {
        throw new Error(
            `Nodo no encontrado para reordenar: ${nodeId}`
        );
    }

    const [node] = list.splice(currentIndex, 1);
    const targetIndex = normalizeIndex(
        index,
        list.length
    );

    list.splice(targetIndex, 0, node);
}

function normalizeIndex(index, max) {
    if (index === null || index === undefined) {
        return max;
    }

    const parsed = Number(index);

    if (!Number.isFinite(parsed)) {
        return max;
    }

    return Math.min(
        Math.max(Math.round(parsed), 0),
        max
    );
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
