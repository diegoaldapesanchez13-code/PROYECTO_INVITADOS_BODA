function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}

function childCollections(node) {
    const collections = [];
    for (const key of ["nodes", "children", "items"]) {
        if (Array.isArray(node?.[key])) collections.push([key, node[key]]);
    }
    return collections;
}

export function findNodeInDocument(document, nodeId) {
    const target = String(nodeId || "");
    if (!target) return null;
    for (const canvas of document?.canvases || []) {
        const found = findNode(canvas.nodes || [], target, null, canvas.id);
        if (found) return found;
    }
    return null;
}

function findNode(nodes, target, parentId, canvasId) {
    for (const node of nodes || []) {
        if (String(node?.id) === target) {
            return { node: clone(node), parentId, canvasId };
        }
        for (const [, children] of childCollections(node)) {
            const found = findNode(children, target, node.id, canvasId);
            if (found) return found;
        }
    }
    return null;
}

export function updateNodeInDocument(document, nodeId, updater) {
    const target = String(nodeId || "");
    let changed = false;
    const canvases = (document?.canvases || []).map((canvas) => ({
        ...canvas,
        nodes: updateNodes(canvas.nodes || [], target, updater, () => { changed = true; }),
    }));
    return { document: { ...document, canvases }, changed };
}

function updateNodes(nodes, target, updater, onChange) {
    return (nodes || []).map((node) => {
        if (String(node?.id) === target) {
            onChange();
            const next = typeof updater === "function" ? updater(clone(node)) : updater;
            return clone(next);
        }
        let nextNode = node;
        for (const [key, children] of childCollections(node)) {
            const nextChildren = updateNodes(children, target, updater, onChange);
            if (nextChildren !== children) nextNode = { ...nextNode, [key]: nextChildren };
        }
        return nextNode;
    });
}
