import { INSPECTOR_DEFAULT_TAB } from "./constants.js";
import { findNodeInDocument, updateNodeInDocument } from "./node_tree.js";
import { getPath, setPathClone } from "./node_path.js";

export class InspectorService {
    #app;
    #registry;
    #selectedNodeId = null;
    #activeTab = INSPECTOR_DEFAULT_TAB;
    #openGroupsByNode = new Map();
    #scrollByNode = new Map();
    #listeners = new Set();

    constructor({ app, registry } = {}) {
        if (!app || typeof app.updateDocument !== "function") {
            throw new TypeError("InspectorService requiere BuilderApp.");
        }
        this.#app = app;
        this.#registry = registry;
    }

    get selectedNodeId() { return this.#selectedNodeId; }
    get activeTab() { return this.#activeTab; }
    get selected() {
        return this.#selectedNodeId
            ? findNodeInDocument(this.#app.getDocument(), this.#selectedNodeId)
            : null;
    }

    select(nodeId) {
        const match = nodeId == null ? null : findNodeInDocument(this.#app.getDocument(), nodeId);
        this.#selectedNodeId = match?.node?.id || null;
        this.#emit("inspector:selected", { nodeId: this.#selectedNodeId, match });
        return match;
    }

    clearSelection() {
        return this.select(null);
    }

    setActiveTab(tab) {
        const next = String(tab || INSPECTOR_DEFAULT_TAB);
        this.#activeTab = next;
        this.#emit("inspector:tab-changed", { tab: next });
        return next;
    }

    panels() {
        const selected = this.selected;
        if (!selected) return [];
        return this.#registry.list({
            node: selected.node,
            canvasId: selected.canvasId,
            parentId: selected.parentId,
            tab: this.#activeTab,
            inspector: this,
        });
    }

    read(path, fallback = undefined) {
        return getPath(this.selected?.node, path, fallback);
    }

    update(path, value, meta = {}) {
        if (!this.#selectedNodeId) return null;
        return this.patch((node) => setPathClone(node, path, value), {
            type: "inspector:property-updated",
            path: Array.isArray(path) ? path.join(".") : String(path),
            ...meta,
        });
    }

    patch(patchOrMutator, meta = {}) {
        if (!this.#selectedNodeId) return null;
        const nodeId = this.#selectedNodeId;
        let changed = false;
        this.#app.updateDocument((document) => {
            const result = updateNodeInDocument(document, nodeId, (node) => {
                const next = typeof patchOrMutator === "function"
                    ? patchOrMutator(node)
                    : { ...node, ...(patchOrMutator || {}) };
                return next || node;
            });
            changed = result.changed;
            return result.document;
        }, { type: meta.type || "inspector:node-updated", nodeId, ...meta });
        if (!changed) return null;
        const selected = this.selected;
        this.#emit(meta.type || "inspector:node-updated", { nodeId, selected, ...meta });
        return selected;
    }

    setGroupOpen(groupId, isOpen) {
        const nodeKey = this.#selectedNodeId || "__empty__";
        const groups = new Map(this.#openGroupsByNode.get(nodeKey) || []);
        groups.set(String(groupId), Boolean(isOpen));
        this.#openGroupsByNode.set(nodeKey, groups);
        this.#emit("inspector:group-state", { nodeId: this.#selectedNodeId, groupId, isOpen: Boolean(isOpen) });
    }

    isGroupOpen(groupId, fallback = true) {
        const groups = this.#openGroupsByNode.get(this.#selectedNodeId || "__empty__");
        return groups?.has(String(groupId)) ? groups.get(String(groupId)) : Boolean(fallback);
    }

    setScroll(position) {
        const key = this.#selectedNodeId || "__empty__";
        const value = Math.max(Number(position) || 0, 0);
        this.#scrollByNode.set(key, value);
        return value;
    }

    getScroll() {
        return this.#scrollByNode.get(this.#selectedNodeId || "__empty__") || 0;
    }

    subscribe(listener) {
        if (typeof listener !== "function") throw new TypeError("listener debe ser una función.");
        this.#listeners.add(listener);
        return () => this.#listeners.delete(listener);
    }

    destroy() {
        this.#listeners.clear();
        this.#openGroupsByNode.clear();
        this.#scrollByNode.clear();
        this.#selectedNodeId = null;
    }

    #emit(type, payload = {}) {
        const event = Object.freeze({ type, payload, service: this });
        for (const listener of this.#listeners) listener(event);
    }
}
