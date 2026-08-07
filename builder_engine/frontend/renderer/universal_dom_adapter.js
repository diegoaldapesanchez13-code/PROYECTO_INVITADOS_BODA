import { executeUniversalAction } from "./universal_interaction_resolver.js";
import { styleToCssObject } from "./universal_style_resolver.js";

export class UniversalDomAdapter {
    #runtime;

    constructor(options = {}) {
        this.#runtime = options.runtime || defaultRuntime();
    }

    mount(result, target) {
        if (!target || typeof target.replaceChildren !== "function") {
            throw new TypeError("UniversalDomAdapter requiere un elemento destino.");
        }

        const fragment = document.createDocumentFragment();
        for (const canvas of result.canvases || []) {
            fragment.append(this.#canvas(canvas, result.mode));
        }

        target.replaceChildren(fragment);
        target.dataset.renderer = "universal";
        target.dataset.renderMode = result.mode;
        target.dataset.device = result.metadata?.device || "mobile";
        return target;
    }

    #canvas(canvas, mode) {
        const element = document.createElement("section");
        element.className = "dirtec-render-canvas";
        element.dataset.canvasId = canvas.id;
        element.dataset.renderMode = mode;
        applyStyle(element, canvas.style);

        for (const child of canvas.children || []) {
            element.append(this.#node(child, mode));
        }
        return element;
    }

    #node(node, mode) {
        const element = document.createElement(node.tag || "div");
        element.classList.add("dirtec-render-node", `dirtec-node-${node.type.toLowerCase()}`);

        for (const [name, value] of Object.entries(node.attributes || {})) {
            if (value === null || value === undefined || value === false) continue;
            if (name in element && name !== "style") {
                try {
                    element[name] = value;
                    continue;
                } catch {}
            }
            element.setAttribute(name, String(value));
        }

        applyStyle(element, node.style);

        if (
            node.content !== null
            && node.content !== undefined
            && !["img", "video"].includes(node.tag)
        ) {
            element.textContent = String(node.content);
        }

        for (const child of node.children || []) {
            element.append(this.#node(child, mode));
        }

        if (node.runtime?.actionable) {
            this.#bindInteraction(element, node, mode);
        }

        return element;
    }

    #bindInteraction(element, node, mode) {
        const interaction = node.runtime?.interaction;
        if (!interaction || mode === "EDIT") return;

        const run = (trigger) => {
            const actions = interaction.interactions
                .filter((entry) => entry.enabled && entry.trigger === trigger);

            for (const entry of actions) {
                executeUniversalAction(entry.action, this.#runtime);
            }
        };

        element.addEventListener("click", (event) => {
            event.preventDefault();
            run("CLICK");
        });

        element.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") return;
            event.preventDefault();
            run("CLICK");
        });
    }
}

function applyStyle(element, style = {}) {
    const normalized = styleToCssObject(style);
    for (const [property, value] of Object.entries(normalized)) {
        if (property.startsWith("--")) {
            element.style.setProperty(property, value);
        } else {
            element.style[property] = value;
        }
    }
}

function defaultRuntime() {
    return {
        openUrl(value, options = {}) {
            if (!value) return;
            window.open(value, options.newTab ? "_blank" : options.target || "_self");
        },
        navigate(value) {
            if (value) window.location.href = value;
        },
        download(value) {
            if (!value) return;
            const link = document.createElement("a");
            link.href = value;
            link.download = "";
            link.click();
        },
    };
}
