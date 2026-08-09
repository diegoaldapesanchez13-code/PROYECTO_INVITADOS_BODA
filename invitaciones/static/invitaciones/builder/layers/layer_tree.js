import {
    NODE_TYPES,
    componentIcon,
} from "../core/index.js";

import {
    LayerStackManager,
} from "./layer_stack.js";

const CONTAINER_TYPES = new Set([
    NODE_TYPES.CANVAS,
    NODE_TYPES.CONTAINER,
    NODE_TYPES.CARD,
    NODE_TYPES.GALLERY,
    NODE_TYPES.RSVP,
]);

export class LayerTree {
    constructor(options = {}) {
        const {
            root,
            state,
            canvas,
            onDocumentChange = null,
            onStatus = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "LayerTree root debe ser un elemento HTML."
            );
        }

        if (!state || !canvas) {
            throw new Error(
                "LayerTree requiere state y canvas."
            );
        }

        this.root = root;
        this.state = state;
        this.canvas = canvas;
        this.onDocumentChange =
            onDocumentChange;
        this.onStatus = onStatus;

        this.stack =
            new LayerStackManager({
                state,
            });

        this.expanded = new Set(
            state.document.canvases.map(
                (canvas) => canvas.id
            )
        );

        this.draggedNodeId = null;

        this.unsubscribe =
            this.state.subscribe(
                (event) => {
                    if (
                        event.type
                        === "selection:change"
                        || event.type
                            === "selection:clear"
                    ) {
                        this.#syncSelection();
                        return;
                    }

                    this.render();
                }
            );

        this.render();
    }

    destroy() {
        this.unsubscribe?.();
        this.root.replaceChildren();
    }

    render() {
        this.root.replaceChildren();
        this.root.classList.add(
            "r3-layer-tree"
        );

        this.root.append(
            this.#renderHeader(),
            this.#renderTree()
        );

        this.#syncSelection();
    }

    reveal(nodeId) {
        let node =
            this.state.getNode(nodeId);

        while (node?.parentId) {
            this.expanded.add(
                node.parentId
            );

            node =
                this.state.getNode(
                    node.parentId
                );
        }

        this.render();

        const row =
            this.root.querySelector(
                `[data-r3-layer-id="${cssEscape(
                    nodeId
                )}"]`
            );

        row?.scrollIntoView({
            block: "nearest",
        });
    }

    #renderHeader() {
        const header =
            document.createElement(
                "header"
            );

        header.className =
            "r3-layer-tree__header";

        const text =
            document.createElement("div");

        text.innerHTML = `
            <strong>Capas</strong>
            <small>Jerarquía real del documento</small>
        `;

        const expandAll =
            document.createElement(
                "button"
            );

        expandAll.type = "button";
        expandAll.textContent = "Expandir";
        expandAll.title =
            "Expandir todas las capas";

        expandAll.addEventListener(
            "click",
            () => {
                for (
                    const node
                    of [
                        ...this.state
                            .document.canvases,
                        ...this.state
                            .document.nodes,
                    ]
                ) {
                    if (
                        node.children?.length
                    ) {
                        this.expanded.add(
                            node.id
                        );
                    }
                }

                this.render();
            }
        );

        header.append(
            text,
            expandAll
        );

        return header;
    }

    #renderTree() {
        const tree =
            document.createElement("div");

        tree.className =
            "r3-layer-tree__body";
        tree.setAttribute(
            "role",
            "tree"
        );

        const canvass =
            [...this.state.document.canvases]
                .sort(
                    (a, b) =>
                        a.order - b.order
                );

        if (!canvass.length) {
            const empty =
                document.createElement("p");

            empty.className =
                "r3-layer-tree__empty";
            empty.textContent =
                "El documento no tiene lienzos.";

            tree.append(empty);
            return tree;
        }

        for (const canvas of canvass) {
            tree.append(
                this.#renderNode(
                    canvas,
                    0
                )
            );
        }

        return tree;
    }

    #renderNode(node, depth) {
        const wrapper =
            document.createElement("div");

        wrapper.className =
            "r3-layer-node";
        wrapper.dataset.r3LayerId =
            node.id;
        wrapper.setAttribute(
            "role",
            "treeitem"
        );
        wrapper.setAttribute(
            "aria-level",
            String(depth + 1)
        );
        wrapper.draggable =
            !node.locked;

        const hasChildren =
            Boolean(
                node.children?.length
            );

        const isExpanded =
            this.expanded.has(
                node.id
            );

        if (hasChildren) {
            wrapper.setAttribute(
                "aria-expanded",
                String(isExpanded)
            );
        }

        const row =
            document.createElement("div");

        row.className =
            "r3-layer-node__row";
        row.style.setProperty(
            "--r3-layer-depth",
            depth
        );

        const toggle =
            document.createElement(
                "button"
            );

        toggle.type = "button";
        toggle.className =
            "r3-layer-node__toggle";
        toggle.textContent =
            hasChildren
                ? (
                    isExpanded
                        ? "▾"
                        : "▸"
                )
                : "·";
        toggle.disabled =
            !hasChildren;
        toggle.title =
            hasChildren
                ? "Expandir o contraer"
                : "";

        toggle.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                if (!hasChildren) {
                    return;
                }

                if (isExpanded) {
                    this.expanded.delete(
                        node.id
                    );
                } else {
                    this.expanded.add(
                        node.id
                    );
                }

                this.render();
            }
        );

        const type =
            document.createElement(
                "span"
            );

        type.className =
            "r3-layer-node__icon";
        type.textContent =
            componentIcon(node.type);
        type.title = node.type;

        const name =
            document.createElement(
                "button"
            );

        name.type = "button";
        name.className =
            "r3-layer-node__name";
        name.textContent =
            node.name || node.type;
        name.title =
            node.name || node.type;

        name.addEventListener(
            "click",
            () => {
                this.canvas.select(
                    node.id
                );

                this.reveal(node.id);
            }
        );

        name.addEventListener(
            "dblclick",
            (event) => {
                event.stopPropagation();
                this.#beginRename(
                    node,
                    name
                );
            }
        );

        const level =
            document.createElement(
                "span"
            );

        level.className =
            "r3-layer-node__level";
        level.textContent =
            String(
                this.stack.levelOf(
                    node
                )
            );
        level.title =
            `Nivel de capa ${level.textContent}`;

        const visibility =
            document.createElement(
                "button"
            );

        visibility.type = "button";
        visibility.className =
            "r3-layer-node__action";
        visibility.textContent =
            node.visible ? "◉" : "○";
        visibility.title =
            node.visible
                ? "Ocultar"
                : "Mostrar";

        visibility.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                this.state.updateNode(
                    node.id,
                    {
                        visible:
                            !node.visible,
                    },
                    {
                        ignoreLock: true,
                    }
                );

                this.#changed(
                    `${node.name}: visibilidad actualizada`
                );
            }
        );

        const lock =
            document.createElement(
                "button"
            );

        lock.type = "button";
        lock.className =
            "r3-layer-node__action";
        lock.textContent =
            node.locked ? "🔒" : "·";
        lock.title =
            node.locked
                ? "Desbloquear"
                : "Bloquear";

        lock.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                this.state.updateNode(
                    node.id,
                    {
                        locked:
                            !node.locked,
                    },
                    {
                        ignoreLock: true,
                    }
                );

                this.#changed(
                    `${node.name}: bloqueo actualizado`
                );
            }
        );

        row.append(
            toggle,
            type,
            name,
            level,
            visibility,
            lock
        );

        row.addEventListener(
            "click",
            () => {
                this.canvas.select(
                    node.id
                );
            }
        );

        this.#bindDragAndDrop(
            wrapper,
            row,
            node
        );

        wrapper.append(row);

        if (
            hasChildren
            && isExpanded
        ) {
            const children =
                document.createElement(
                    "div"
                );

            children.className =
                "r3-layer-node__children";
            children.setAttribute(
                "role",
                "group"
            );

            for (
                const child
                of this.stack
                    .childrenFrontToBack(
                        node.id
                    )
            ) {
                children.append(
                    this.#renderNode(
                        child,
                        depth + 1
                    )
                );
            }

            wrapper.append(children);
        }

        return wrapper;
    }

    #bindDragAndDrop(
        wrapper,
        row,
        node
    ) {
        wrapper.addEventListener(
            "dragstart",
            (event) => {
                if (node.locked) {
                    event.preventDefault();
                    return;
                }

                this.draggedNodeId =
                    node.id;

                event.dataTransfer
                    ?.setData(
                        "application/x-r3-layer",
                        node.id
                    );

                if (event.dataTransfer) {
                    event.dataTransfer
                        .effectAllowed =
                            "move";
                }

                row.classList.add(
                    "is-dragging"
                );
            }
        );

        wrapper.addEventListener(
            "dragend",
            () => {
                this.draggedNodeId =
                    null;

                this.root
                    .querySelectorAll(
                        ".is-dragging, .is-drop-target"
                    )
                    .forEach(
                        (element) =>
                            element.classList
                                .remove(
                                    "is-dragging",
                                    "is-drop-target"
                                )
                    );
            }
        );

        row.addEventListener(
            "dragover",
            (event) => {
                const draggedId =
                    event.dataTransfer
                        ?.getData(
                            "application/x-r3-layer"
                        )
                    || this.draggedNodeId;

                if (
                    !draggedId
                    || draggedId === node.id
                ) {
                    return;
                }

                event.preventDefault();
                row.classList.add(
                    "is-drop-target"
                );

                if (event.dataTransfer) {
                    event.dataTransfer
                        .dropEffect =
                            "move";
                }
            }
        );

        row.addEventListener(
            "dragleave",
            () => {
                row.classList.remove(
                    "is-drop-target"
                );
            }
        );

        row.addEventListener(
            "drop",
            (event) => {
                event.preventDefault();
                event.stopPropagation();

                row.classList.remove(
                    "is-drop-target"
                );

                const draggedId =
                    event.dataTransfer
                        ?.getData(
                            "application/x-r3-layer"
                        )
                    || this.draggedNodeId;

                if (
                    !draggedId
                    || draggedId === node.id
                ) {
                    return;
                }

                this.#dropNode(
                    draggedId,
                    node,
                    event
                );
            }
        );
    }

    #dropNode(
        draggedId,
        target,
        event
    ) {
        const dragged =
            this.state.getNode(
                draggedId
            );

        if (!dragged) {
            return;
        }

        try {
            if (
                dragged.type
                === NODE_TYPES.CANVAS
            ) {
                if (
                    target.type
                    !== NODE_TYPES.CANVAS
                ) {
                    throw new Error(
                        "Una sección solo puede reordenarse entre secciones."
                    );
                }

                this.state.reorderNode(
                    dragged.id,
                    target.order
                );
            } else {
                const rect =
                    event.currentTarget
                        .getBoundingClientRect();

                const relativeY =
                    event.clientY
                    - rect.top;

                const wantsInside =
                    CONTAINER_TYPES.has(
                        target.type
                    )
                    && relativeY
                        > rect.height * .28
                    && relativeY
                        < rect.height * .72;

                if (wantsInside) {
                    this.stack.moveInside({
                        draggedId:
                            dragged.id,
                        parentId:
                            target.id,
                        front: true,
                    });

                    this.expanded.add(
                        target.id
                    );
                } else {
                    if (!target.parentId) {
                        throw new Error(
                            "No se puede colocar el nodo fuera de una sección."
                        );
                    }

                    if (
                        dragged.parentId
                        !== target.parentId
                    ) {
                        this.state.moveNode(
                            dragged.id,
                            target.parentId,
                            null
                        );
                    }

                    this.stack.moveRelative({
                        draggedId:
                            dragged.id,
                        targetId:
                            target.id,
                        placement:
                            relativeY
                            < rect.height / 2
                                ? "FRONT"
                                : "BEHIND",
                    });
                }
            }

            this.#changed(
                `${dragged.name} reordenado`
            );

            this.canvas.select(
                dragged.id
            );
        } catch (error) {
            this.onStatus?.(
                error.message
            );
        }
    }

    #beginRename(node, button) {
        const input =
            document.createElement(
                "input"
            );

        input.className =
            "r3-layer-node__rename";
        input.value =
            node.name || "";
        input.setAttribute(
            "aria-label",
            "Nuevo nombre"
        );

        const commit =
            () => {
                const value =
                    input.value.trim();

                if (
                    value
                    && value !== node.name
                ) {
                    this.state.updateNode(
                        node.id,
                        {
                            name: value,
                        },
                        {
                            ignoreLock: true,
                        }
                    );

                    this.#changed(
                        "Nombre actualizado"
                    );
                } else {
                    this.render();
                }
            };

        input.addEventListener(
            "keydown",
            (event) => {
                if (
                    event.key === "Enter"
                ) {
                    commit();
                }

                if (
                    event.key === "Escape"
                ) {
                    this.render();
                }
            }
        );

        input.addEventListener(
            "blur",
            commit,
            {
                once: true,
            }
        );

        button.replaceWith(input);
        input.focus();
        input.select();
    }

    #changed(message) {
        this.onDocumentChange?.();
        this.onStatus?.(message);
        this.render();
    }

    #syncSelection() {
        const selectedId =
            this.state.selection.nodeId;

        this.root
            .querySelectorAll(
                "[data-r3-layer-id]"
            )
            .forEach((element) => {
                element.classList.toggle(
                    "is-selected",
                    element.dataset.r3LayerId
                        === selectedId
                );
            });

        if (selectedId) {
            const selected =
                this.root.querySelector(
                    `[data-r3-layer-id="${cssEscape(
                        selectedId
                    )}"]`
                );

            selected?.scrollIntoView({
                block: "nearest",
            });
        }
    }
}

function cssEscape(value) {
    if (
        globalThis.CSS
        && typeof CSS.escape
            === "function"
    ) {
        return CSS.escape(
            String(value)
        );
    }

    return String(value)
        .replace(
            /["\\]/g,
            "\\$&"
        );
}
