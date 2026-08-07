export const LAYER_STACK_VERSION = 2;

export class LayerStackService {
    normalize(nodes = []) {
        const draft = cloneNodes(nodes);
        normalizeRecursive(draft);
        return draft;
    }

    listBackToFront(nodes = []) {
        return cloneNodes(nodes);
    }

    listFrontToBack(nodes = []) {
        return cloneNodes(nodes).reverse();
    }

    bringForward(nodes, nodeId) {
        return mutateSiblingOrder(nodes, nodeId, (siblings, index) => {
            if (index >= siblings.length - 1) return false;
            swap(siblings, index, index + 1);
            return true;
        });
    }

    sendBackward(nodes, nodeId) {
        return mutateSiblingOrder(nodes, nodeId, (siblings, index) => {
            if (index <= 0) return false;
            swap(siblings, index, index - 1);
            return true;
        });
    }

    bringToFront(nodes, nodeId) {
        return mutateSiblingOrder(nodes, nodeId, (siblings, index) => {
            if (index === siblings.length - 1) return false;
            const [node] = siblings.splice(index, 1);
            siblings.push(node);
            return true;
        });
    }

    sendToBack(nodes, nodeId) {
        return mutateSiblingOrder(nodes, nodeId, (siblings, index) => {
            if (index === 0) return false;
            const [node] = siblings.splice(index, 1);
            siblings.unshift(node);
            return true;
        });
    }

    moveBefore(nodes, nodeId, targetId) {
        return moveRelative(nodes, nodeId, targetId, "BEFORE");
    }

    moveAfter(nodes, nodeId, targetId) {
        return moveRelative(nodes, nodeId, targetId, "AFTER");
    }

    moveInside(nodes, nodeId, parentId, options = {}) {
        const draft = cloneNodes(nodes);
        const source = findLocation(draft, nodeId);
        const parent = findNode(draft, parentId);

        if (!source) throw new Error("No se encontró la capa origen.");
        if (!parent) throw new Error("No se encontró el contenedor destino.");
        if (!acceptsChildren(parent)) {
            throw new Error("La capa destino no acepta elementos hijos.");
        }
        if (source.node.id === parent.id || containsNode(source.node, parent.id)) {
            throw new Error("No se puede mover una capa dentro de sí misma.");
        }
        if (source.node.locked && !options.ignoreLock) {
            throw new Error("La capa está bloqueada.");
        }

        const [detached] = source.siblings.splice(source.index, 1);
        parent.children = Array.isArray(parent.children) ? parent.children : [];

        if (String(options.placement || "FRONT").toUpperCase() === "BACK") {
            parent.children.unshift(detached);
        } else {
            parent.children.push(detached);
        }

        normalizeRecursive(draft);

        return result(draft, {
            operation: "MOVE_INSIDE",
            nodeId,
            sourceParentId: source.parentId,
            targetParentId: parentId,
            changed: true,
        });
    }

    remove(nodes, nodeId, options = {}) {
        const draft = cloneNodes(nodes);
        const location = findLocation(draft, nodeId);
        if (!location) throw new Error("No se encontró la capa.");
        if (location.node.locked && !options.ignoreLock) {
            throw new Error("La capa está bloqueada.");
        }

        const [removed] = location.siblings.splice(location.index, 1);
        normalizeRecursive(draft);

        return {
            ...result(draft, {
                operation: "REMOVE",
                nodeId,
                sourceParentId: location.parentId,
                changed: true,
            }),
            removed,
        };
    }

    duplicate(nodes, nodeId, options = {}) {
        const draft = cloneNodes(nodes);
        const location = findLocation(draft, nodeId);
        if (!location) throw new Error("No se encontró la capa.");

        const duplicate = regenerateIds(
            clone(location.node),
            options.idFactory || defaultId,
        );
        duplicate.name = options.name || `${location.node.name || "Capa"} copia`;

        location.siblings.splice(location.index + 1, 0, duplicate);
        normalizeRecursive(draft);

        return {
            ...result(draft, {
                operation: "DUPLICATE",
                nodeId: duplicate.id,
                sourceNodeId: nodeId,
                targetParentId: location.parentId,
                changed: true,
            }),
            duplicate,
        };
    }

    setVisibility(nodes, nodeId, visible) {
        return updateNode(nodes, nodeId, (node) => {
            node.visible = Boolean(visible);
        }, "SET_VISIBILITY");
    }

    setLocked(nodes, nodeId, locked) {
        return updateNode(nodes, nodeId, (node) => {
            node.locked = Boolean(locked);
        }, "SET_LOCKED");
    }

    rename(nodes, nodeId, name) {
        const clean = String(name || "").trim();
        if (!clean) throw new Error("El nombre no puede estar vacío.");

        return updateNode(nodes, nodeId, (node) => {
            node.name = clean;
        }, "RENAME");
    }

    parentOf(nodes, nodeId) {
        return findLocation(nodes, nodeId)?.parentId ?? null;
    }

    siblingsOf(nodes, nodeId) {
        const location = findLocation(nodes, nodeId);
        return location ? cloneNodes(location.siblings) : [];
    }

    flatten(nodes = [], options = {}) {
        const frontToBack = options.frontToBack !== false;
        const expanded = options.expanded || null;
        const output = [];

        const visit = (siblings, parentId = null, depth = 0) => {
            const ordered = frontToBack ? [...siblings].reverse() : [...siblings];

            for (const node of ordered) {
                const children = Array.isArray(node.children) ? node.children : [];
                output.push({
                    id: node.id,
                    parentId,
                    depth,
                    name: node.name || node.type || node.id,
                    type: node.type || "UNKNOWN",
                    visible: node.visible !== false,
                    locked: Boolean(node.locked),
                    expandable: children.length > 0,
                    expanded: expanded ? expanded.has(node.id) : true,
                    zIndex: Number(node.style?.zIndex || 0),
                    node: clone(node),
                });

                if (children.length && (!expanded || expanded.has(node.id))) {
                    visit(children, node.id, depth + 1);
                }
            }
        };

        visit(nodes);
        return output;
    }

    validate(nodes = []) {
        const errors = [];
        const ids = new Set();

        const visit = (siblings, parentId = null) => {
            siblings.forEach((node, index) => {
                if (!node?.id) {
                    errors.push(`Nodo sin id dentro de ${parentId || "canvas"}.`);
                    return;
                }
                if (ids.has(node.id)) errors.push(`ID duplicado: ${node.id}.`);
                ids.add(node.id);

                const expectedZ = index + 1;
                const actualZ = Number(node.style?.zIndex || 0);
                if (actualZ !== expectedZ) {
                    errors.push(
                        `Orden inconsistente en ${node.id}: zIndex=${actualZ}, esperado=${expectedZ}.`
                    );
                }

                if (node.style?.responsive) {
                    for (const [device, values] of Object.entries(node.style.responsive)) {
                        if (values && Object.hasOwn(values, "zIndex")) {
                            errors.push(
                                `zIndex responsive no permitido en ${node.id}.${device}.`
                            );
                        }
                    }
                }

                visit(Array.isArray(node.children) ? node.children : [], node.id);
            });
        };

        visit(nodes);
        return { valid: errors.length === 0, errors };
    }
}

function mutateSiblingOrder(nodes, nodeId, operation) {
    const draft = cloneNodes(nodes);
    const location = findLocation(draft, nodeId);

    if (!location) throw new Error("No se encontró la capa.");
    if (location.node.locked) throw new Error("La capa está bloqueada.");

    const changed = operation(location.siblings, location.index);
    normalizeRecursive(draft);

    return result(draft, {
        operation: "REORDER",
        nodeId,
        sourceParentId: location.parentId,
        targetParentId: location.parentId,
        changed,
    });
}

function moveRelative(nodes, nodeId, targetId, placement) {
    if (nodeId === targetId) {
        return result(cloneNodes(nodes), {
            operation: "MOVE_RELATIVE",
            nodeId,
            targetId,
            changed: false,
        });
    }

    const draft = cloneNodes(nodes);
    const source = findLocation(draft, nodeId);
    const targetBeforeDetach = findLocation(draft, targetId);

    if (!source || !targetBeforeDetach) {
        throw new Error("No se encontró la capa origen o destino.");
    }
    if (source.node.locked) throw new Error("La capa está bloqueada.");
    if (source.parentId !== targetBeforeDetach.parentId) {
        throw new Error("Las capas deben compartir el mismo contenedor.");
    }

    const [detached] = source.siblings.splice(source.index, 1);
    const target = findLocation(draft, targetId);
    const insertAt = placement === "AFTER" ? target.index + 1 : target.index;

    target.siblings.splice(insertAt, 0, detached);
    normalizeRecursive(draft);

    return result(draft, {
        operation: `MOVE_${placement}`,
        nodeId,
        targetId,
        sourceParentId: source.parentId,
        targetParentId: target.parentId,
        changed: true,
    });
}

function updateNode(nodes, nodeId, updater, operation) {
    const draft = cloneNodes(nodes);
    const location = findLocation(draft, nodeId);
    if (!location) throw new Error("No se encontró la capa.");

    updater(location.node);
    normalizeRecursive(draft);

    return result(draft, {
        operation,
        nodeId,
        sourceParentId: location.parentId,
        targetParentId: location.parentId,
        changed: true,
    });
}

function normalizeRecursive(nodes) {
    nodes.forEach((node, index) => {
        node.style = { ...(node.style || {}), zIndex: index + 1 };

        if (node.style.responsive) {
            node.style.responsive = stripResponsiveZIndex(node.style.responsive);
        }

        node.children = Array.isArray(node.children) ? node.children : [];
        normalizeRecursive(node.children);
    });
}

function stripResponsiveZIndex(responsive) {
    const clean = {};
    for (const [device, values] of Object.entries(responsive || {})) {
        const { zIndex, ...rest } = values || {};
        clean[device] = rest;
    }
    return clean;
}

function findLocation(nodes, nodeId, parentId = null) {
    for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];

        if (node.id === nodeId) {
            return { node, siblings: nodes, index, parentId };
        }

        const nested = findLocation(
            Array.isArray(node.children) ? node.children : [],
            nodeId,
            node.id,
        );
        if (nested) return nested;
    }
    return null;
}

function findNode(nodes, nodeId) {
    return findLocation(nodes, nodeId)?.node || null;
}

function containsNode(node, nodeId) {
    if (node.id === nodeId) return true;
    return (node.children || []).some((child) => containsNode(child, nodeId));
}

function acceptsChildren(node) {
    return ["CONTAINER", "CARD", "GROUP", "COUNTDOWN", "CANVAS"]
        .includes(String(node.type || "").toUpperCase())
        || node.acceptsChildren === true;
}

function swap(values, first, second) {
    [values[first], values[second]] = [values[second], values[first]];
}

/**
 * Resultado compatible del LayerStack.
 *
 * Se retorna el propio arreglo para conservar el contrato histórico:
 * `result.map(...)`, `result.length`, `result[index]`.
 *
 * El mismo arreglo expone además:
 * `result.nodes` y `result.transaction`.
 */
function result(nodes, metadata) {
    const transaction = Object.freeze({
        ...metadata,
        timestamp: Date.now(),
    });

    Object.defineProperties(nodes, {
        nodes: {
            value: nodes,
            enumerable: false,
            configurable: false,
            writable: false,
        },
        transaction: {
            value: transaction,
            enumerable: false,
            configurable: false,
            writable: false,
        },
    });

    return nodes;
}

function regenerateIds(node, idFactory) {
    node.id = idFactory(node);
    node.children = (node.children || []).map((child) =>
        regenerateIds(child, idFactory)
    );
    return node;
}

function defaultId(node) {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return `${String(node.type || "node").toLowerCase()}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function cloneNodes(nodes) {
    return clone(nodes || []);
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
