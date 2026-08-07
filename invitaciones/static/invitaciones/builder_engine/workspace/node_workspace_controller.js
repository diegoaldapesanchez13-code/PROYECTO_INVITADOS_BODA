export class NodeWorkspaceController {
    #app;
    #workspace;
    #canvasController;
    #selectedNodeId = null;

    constructor({ app, workspace, canvasController }) {
        if (!app?.getDocument || !app?.updateDocument) {
            throw new TypeError("NodeWorkspaceController requiere BuilderApp.");
        }
        if (!canvasController?.getSelected) {
            throw new TypeError("NodeWorkspaceController requiere CanvasWorkspaceController.");
        }
        this.#app = app;
        this.#workspace = workspace || null;
        this.#canvasController = canvasController;
    }

    get selectedNodeId() {
        return this.#selectedNodeId;
    }

    initialize() {
        const preferred = this.#workspace?.value?.selectedNodeId;
        const exists = preferred && this.find(preferred);
        this.select(exists ? preferred : null);
        return this;
    }

    select(nodeId) {
        this.#selectedNodeId = nodeId && this.find(nodeId) ? nodeId : null;

        this.#workspace?.update((state) => {
            state.selectedNodeId = this.#selectedNodeId;
        });

        return this.getSelected();
    }

    getSelected() {
        return this.find(this.#selectedNodeId);
    }

    listTree() {
        const canvas = this.#canvasController.getSelected();
        return clone(canvas?.nodes || []);
    }

    find(nodeId) {
        if (!nodeId) return null;
        return findNode(this.listTree(), nodeId)?.node || null;
    }

    update(path, value, meta = {}) {
        const nodeId = this.#selectedNodeId;
        if (!nodeId) throw new Error("No hay un elemento seleccionado.");

        this.#app.updateDocument((document) => {
            const canvas = document.canvases.find(
                (item) => item.id === this.#canvasController.selectedCanvasId,
            );
            if (!canvas) throw new Error("Lienzo no encontrado.");

            const match = findNode(canvas.nodes || [], nodeId);
            if (!match) throw new Error("Elemento no encontrado.");

            setByPath(match.node, path, value);
        }, {
            label: meta.label || "Editar elemento",
            source: "node-inspector",
            mergeKey: meta.mergeKey || `node:${nodeId}:${path}`,
        });

        return this.getSelected();
    }

    rename(name) {
        const clean = String(name || "").trim();
        if (!clean) throw new Error("El nombre es obligatorio.");
        return this.update("name", clean.slice(0, 120), {
            label: "Renombrar elemento",
        });
    }

    toggleVisibility() {
        const node = this.getSelected();
        if (!node) throw new Error("No hay un elemento seleccionado.");
        return this.update("visible", node.visible === false, {
            label: "Cambiar visibilidad",
            mergeKey: null,
        });
    }

    toggleLock() {
        const node = this.getSelected();
        if (!node) throw new Error("No hay un elemento seleccionado.");
        return this.update("locked", !node.locked, {
            label: "Cambiar bloqueo",
            mergeKey: null,
        });
    }

    setZIndex(value) { const parsed=Number(value); if(!Number.isFinite(parsed)) throw new Error("Z-index inválido."); return this.update("style.zIndex",Math.round(parsed),{label:"Cambiar orden de capa",mergeKey:null}); }
    moveLayer(direction) { const node=this.getSelected(); if(!node) throw new Error("No hay un elemento seleccionado."); const flat=flattenNodes(this.listTree()),vals=flat.map(i=>Number(i.style?.zIndex||0)),cur=Number(node.style?.zIndex||0),min=vals.length?Math.min(...vals):0,max=vals.length?Math.max(...vals):0; const next={front:max+1,back:min-1,up:cur+1,down:cur-1}[direction]; if(next===undefined)throw new Error("Dirección de capa inválida."); return this.setZIndex(next); }

    remove() {
        const nodeId = this.#selectedNodeId;
        if (!nodeId) throw new Error("No hay un elemento seleccionado.");

        this.#app.updateDocument((document) => {
            const canvas = document.canvases.find(
                (item) => item.id === this.#canvasController.selectedCanvasId,
            );
            if (!canvas) throw new Error("Lienzo no encontrado.");
            const removed = removeNode(canvas.nodes || [], nodeId);
            if (!removed) throw new Error("Elemento no encontrado.");
        }, {
            label: "Eliminar elemento",
            source: "node-inspector",
        });

        this.select(null);
        return true;
    }
}

function flattenNodes(nodes=[]){return nodes.flatMap(node=>[node,...flattenNodes(node.children||[])]);}

function findNode(nodes, nodeId, parent = null) {
    for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];
        if (node.id === nodeId) return { node, parent, index, collection: nodes };
        const nested = findNode(node.children || [], nodeId, node);
        if (nested) return nested;
    }
    return null;
}

function removeNode(nodes, nodeId) {
    for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];
        if (node.id === nodeId) {
            nodes.splice(index, 1);
            return true;
        }
        if (removeNode(node.children || [], nodeId)) return true;
    }
    return false;
}

function setByPath(target, path, value) {
    const parts = String(path || "").split(".").filter(Boolean);
    if (!parts.length) throw new Error("Ruta de propiedad inválida.");

    let cursor = target;
    for (const part of parts.slice(0, -1)) {
        if (!cursor[part] || typeof cursor[part] !== "object") {
            cursor[part] = {};
        }
        cursor = cursor[part];
    }
    cursor[parts.at(-1)] = value;
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
