export class LayerStackService {
    normalize(nodes = []) {
        const normalized = clone(nodes);
        normalizeCollection(normalized);
        return normalized;
    }

    bringForward(nodes, nodeId) {
        return mutate(nodes, (collection, index) => {
            if (index < collection.length - 1) {
                [collection[index], collection[index + 1]] = [
                    collection[index + 1],
                    collection[index],
                ];
            }
        }, nodeId);
    }

    sendBackward(nodes, nodeId) {
        return mutate(nodes, (collection, index) => {
            if (index > 0) {
                [collection[index], collection[index - 1]] = [
                    collection[index - 1],
                    collection[index],
                ];
            }
        }, nodeId);
    }

    bringToFront(nodes, nodeId) {
        return mutate(nodes, (collection, index) => {
            const [node] = collection.splice(index, 1);
            collection.push(node);
        }, nodeId);
    }

    sendToBack(nodes, nodeId) {
        return mutate(nodes, (collection, index) => {
            const [node] = collection.splice(index, 1);
            collection.unshift(node);
        }, nodeId);
    }

    moveBefore(nodes, nodeId, targetId) {
        return moveRelative(nodes, nodeId, targetId, "before");
    }

    moveAfter(nodes, nodeId, targetId) {
        return moveRelative(nodes, nodeId, targetId, "after");
    }

    moveInside(nodes, nodeId, parentId) {
        const draft = clone(nodes);
        const detached = detachNode(draft, nodeId);
        if (!detached) throw new Error("Nodo no encontrado.");

        const parent = findNode(draft, parentId);
        if (!parent) throw new Error("Contenedor destino no encontrado.");
        if (!Array.isArray(parent.children)) parent.children = [];
        if (containsNode(detached, parentId)) {
            throw new Error("No se puede mover un nodo dentro de sí mismo.");
        }

        parent.children.push(detached);
        normalizeCollection(draft);
        return draft;
    }

    listFrontToBack(nodes = []) {
        return [...nodes].reverse().map(clone);
    }
}

function mutate(nodes, operation, nodeId) {
    const draft = clone(nodes);
    const location = findLocation(draft, nodeId);
    if (!location) throw new Error("Nodo no encontrado.");
    operation(location.collection, location.index);
    normalizeCollection(draft);
    return draft;
}

function moveRelative(nodes, nodeId, targetId, direction) {
    if (nodeId === targetId) return clone(nodes);

    const draft = clone(nodes);
    const source = detachNode(draft, nodeId);
    if (!source) throw new Error("Nodo origen no encontrado.");

    const target = findLocation(draft, targetId);
    if (!target) throw new Error("Nodo destino no encontrado.");

    const insertion = direction === "after" ? target.index + 1 : target.index;
    target.collection.splice(insertion, 0, source);
    normalizeCollection(draft);
    return draft;
}

function normalizeCollection(nodes) {
    nodes.forEach((node, index) => {
        node.style = {
            ...(node.style || {}),
            zIndex: index + 1,
        };
        if (node.style.responsive) {
            node.style.responsive = stripResponsiveZIndex(node.style.responsive);
        }
        if (Array.isArray(node.children)) normalizeCollection(node.children);
    });
}

function stripResponsiveZIndex(responsive) {
    const result = {};
    for (const [device, values] of Object.entries(responsive || {})) {
        const { zIndex, ...rest } = values || {};
        result[device] = rest;
    }
    return result;
}

function detachNode(nodes, nodeId) {
    for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];
        if (node.id === nodeId) {
            return nodes.splice(index, 1)[0];
        }
        const nested = detachNode(node.children || [], nodeId);
        if (nested) return nested;
    }
    return null;
}

function findLocation(nodes, nodeId) {
    for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];
        if (node.id === nodeId) return { collection: nodes, index, node };
        const nested = findLocation(node.children || [], nodeId);
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

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
