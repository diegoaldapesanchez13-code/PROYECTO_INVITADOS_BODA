function applyStyle(element, style = {}) {
    for (const [property, value] of Object.entries(style)) {
        if (value === null || value === undefined) continue;
        if (property.startsWith("--")) element.style.setProperty(property, String(value));
        else element.style[property] = typeof value === "number" && !unitless.has(property)
            ? `${value}px`
            : String(value);
    }
}

const unitless = new Set(["opacity", "zIndex", "fontWeight", "lineHeight", "flex", "order"]);

export class DomRenderAdapter {
    mount(result, target) {
        if (!target || typeof target.replaceChildren !== "function") {
            throw new TypeError("DomRenderAdapter requiere un elemento destino.");
        }
        const fragment = document.createDocumentFragment();
        for (const canvas of result.canvases || []) fragment.append(this.#canvas(canvas, result.mode));
        target.replaceChildren(fragment);
        target.dataset.renderMode = result.mode;
        return target;
    }

    #canvas(canvas, mode) {
        const element = document.createElement("section");
        element.dataset.canvasId = canvas.id;
        element.dataset.renderMode = mode;
        element.style.position = "relative";
        element.style.width = `${canvas.width}px`;
        element.style.height = `${canvas.height}px`;
        applyStyle(element, canvas.style);
        for (const child of canvas.children || []) element.append(this.#node(child));
        return element;
    }

    #node(node) {
        const element = document.createElement(node.tag || "div");
        for (const [name, value] of Object.entries(node.attributes || {})) {
            if (value === false || value === null || value === undefined) continue;
            if (name in element && name !== "style") {
                try { element[name] = value; continue; } catch {}
            }
            element.setAttribute(name, String(value));
        }
        applyStyle(element, node.style);
        if (node.content !== null && node.content !== undefined && node.tag !== "img") {
            element.textContent = String(node.content);
        }
        for (const child of node.children || []) element.append(this.#node(child));
        return element;
    }
}
