import { LAYOUT_MODES } from "./constants.js";

export class TransformPolicyRegistry {
    #policies = new Map();

    constructor(options = {}) {
        this.register("*", defaultPolicy);
        for (const [type, policy] of Object.entries(options.policies || {})) {
            this.register(type, policy);
        }
    }

    register(type, policy) {
        if (typeof policy !== "function") {
            throw new TypeError("La política debe ser una función.");
        }
        this.#policies.set(normalizeType(type), policy);
        return this;
    }

    resolve(node = {}, context = {}) {
        const type = normalizeType(node.type || "*");
        const policy = this.#policies.get(type) || this.#policies.get("*");
        return Object.freeze({
            ...defaultPolicy(node, context),
            ...policy(node, context),
        });
    }
}

function defaultPolicy(node = {}) {
    const locked = Boolean(node.locked);
    const flow = String(node.layout?.layoutMode || node.layoutMode || "")
        .toUpperCase() === LAYOUT_MODES.FLOW;

    return {
        selectable: true,
        movable: !locked && !flow,
        resizable: !locked,
        rotatable: !locked && !flow,
        backgroundPan: false,
        structural: false,
        reason: locked ? "LOCKED" : flow ? "FLOW_MANAGED" : "FREE_LAYER",
    };
}

function normalizeType(value) {
    return String(value || "*").trim().toUpperCase() || "*";
}
