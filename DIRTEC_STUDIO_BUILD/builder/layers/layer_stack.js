export class LayerStackManager {
    constructor(options = {}) {
        const {
            state,
        } = options;

        if (!state) {
            throw new Error(
                "LayerStackManager requiere state."
            );
        }

        this.state = state;
    }

    childrenFrontToBack(parentId) {
        return this.state
            .getChildren(parentId)
            .sort(compareFrontToBack);
    }

    levelOf(node) {
        return Math.max(
            Number(node?.zIndex ?? 0),
            0
        );
    }

    normalizeParent(parentId) {
        const siblings =
            this.state
                .getChildren(parentId)
                .sort(compareBackToFront);

        this.state.transaction(
            "layers:normalize",
            () => {
                siblings.forEach(
                    (node, index) => {
                        const level =
                            index + 1;

                        if (
                            node.zIndex
                            !== level
                        ) {
                            this.state
                                .updateNode(
                                    node.id,
                                    {
                                        zIndex:
                                            level,
                                    },
                                    {
                                        ignoreLock:
                                            true,
                                    }
                                );
                        }
                    }
                );
            }
        );

        return this.childrenFrontToBack(
            parentId
        );
    }

    moveRelative({
        draggedId,
        targetId,
        placement,
    }) {
        const dragged =
            this.state.getNode(
                draggedId
            );

        const target =
            this.state.getNode(
                targetId
            );

        if (!dragged || !target) {
            throw new Error(
                "No se encontró la capa origen o destino."
            );
        }

        if (
            dragged.parentId
            !== target.parentId
        ) {
            throw new Error(
                "Las capas deben compartir el mismo contenedor."
            );
        }

        const parentId =
            target.parentId;

        const visual =
            this.childrenFrontToBack(
                parentId
            )
                .filter(
                    (node) =>
                        node.id
                        !== dragged.id
                );

        const targetIndex =
            visual.findIndex(
                (node) =>
                    node.id
                    === target.id
            );

        if (targetIndex < 0) {
            throw new Error(
                "La capa destino no pertenece al contenedor."
            );
        }

        const insertIndex =
            placement === "BEHIND"
                ? targetIndex + 1
                : targetIndex;

        visual.splice(
            insertIndex,
            0,
            dragged
        );

        this.#applyVisualOrder(
            parentId,
            visual
        );

        return this.state.getNode(
            draggedId
        );
    }

    moveInside({
        draggedId,
        parentId,
        front = true,
    }) {
        const dragged =
            this.state.getNode(
                draggedId
            );

        if (!dragged) {
            throw new Error(
                "No se encontró la capa."
            );
        }

        this.state.transaction(
            "layers:move-inside",
            () => {
                this.state.moveNode(
                    dragged.id,
                    parentId,
                    null
                );

                const visual =
                    this.childrenFrontToBack(
                        parentId
                    ).filter(
                        (node) =>
                            node.id
                            !== dragged.id
                    );

                if (front) {
                    visual.unshift(
                        this.state.getNode(
                            dragged.id
                        )
                    );
                } else {
                    visual.push(
                        this.state.getNode(
                            dragged.id
                        )
                    );
                }

                this.#applyVisualOrder(
                    parentId,
                    visual
                );
            }
        );

        return this.state.getNode(
            draggedId
        );
    }

    bringForward(nodeId) {
        return this.#step(
            nodeId,
            -1
        );
    }

    sendBackward(nodeId) {
        return this.#step(
            nodeId,
            1
        );
    }

    bringToFront(nodeId) {
        return this.#edge(
            nodeId,
            true
        );
    }

    sendToBack(nodeId) {
        return this.#edge(
            nodeId,
            false
        );
    }

    #step(nodeId, delta) {
        const node =
            this.state.getNode(nodeId);

        if (!node?.parentId) {
            return node;
        }

        const visual =
            this.childrenFrontToBack(
                node.parentId
            );

        const current =
            visual.findIndex(
                (item) =>
                    item.id === node.id
            );

        const next =
            clamp(
                current + delta,
                0,
                visual.length - 1
            );

        if (current === next) {
            return node;
        }

        visual.splice(current, 1);
        visual.splice(next, 0, node);

        this.#applyVisualOrder(
            node.parentId,
            visual
        );

        return this.state.getNode(
            nodeId
        );
    }

    #edge(nodeId, front) {
        const node =
            this.state.getNode(nodeId);

        if (!node?.parentId) {
            return node;
        }

        const visual =
            this.childrenFrontToBack(
                node.parentId
            ).filter(
                (item) =>
                    item.id !== node.id
            );

        if (front) {
            visual.unshift(node);
        } else {
            visual.push(node);
        }

        this.#applyVisualOrder(
            node.parentId,
            visual
        );

        return this.state.getNode(
            nodeId
        );
    }

    #applyVisualOrder(
        parentId,
        frontToBack
    ) {
        const backToFront =
            [...frontToBack]
                .reverse();

        this.state.transaction(
            "layers:reorder",
            () => {
                backToFront.forEach(
                    (node, index) => {
                        this.state
                            .reorderNode(
                                node.id,
                                index
                            );
                    }
                );

                backToFront.forEach(
                    (node, index) => {
                        this.state
                            .updateNode(
                                node.id,
                                {
                                    zIndex:
                                        index + 1,
                                },
                                {
                                    ignoreLock:
                                        true,
                                }
                            );
                    }
                );
            }
        );
    }
}

export function compareFrontToBack(
    a,
    b
) {
    return (
        Number(b.zIndex ?? 0)
        - Number(a.zIndex ?? 0)
        || Number(b.order ?? 0)
        - Number(a.order ?? 0)
    );
}

export function compareBackToFront(
    a,
    b
) {
    return (
        Number(a.zIndex ?? 0)
        - Number(b.zIndex ?? 0)
        || Number(a.order ?? 0)
        - Number(b.order ?? 0)
    );
}

function clamp(value, min, max) {
    return Math.min(
        Math.max(value, min),
        max
    );
}