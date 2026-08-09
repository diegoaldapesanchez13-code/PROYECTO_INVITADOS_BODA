import {
    listInsertableComponents,
} from "./catalog.js?v=f4-native-v4-freeze";

import {
    insertComponent,
} from "./factory.js?v=f4-native-v4-freeze";

export class ComponentLibrary {
    constructor(options = {}) {
        const {
            root,
            state,
            renderer,
            canvas,
            inspector = null,
            onStatus = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "ComponentLibrary root debe ser un elemento HTML."
            );
        }

        if (!state || !renderer || !canvas) {
            throw new Error(
                "ComponentLibrary requiere state, renderer y canvas."
            );
        }

        this.root = root;
        this.state = state;
        this.renderer = renderer;
        this.canvas = canvas;
        this.inspector = inspector;
        this.onStatus = onStatus;

        this.render();
    }

    setInspector(inspector) {
        this.inspector = inspector;
    }

    render() {
        this.root.replaceChildren();
        this.root.classList.add("r3-component-library");

        const header = document.createElement("header");
        header.className = "r3-component-library__header";
        header.innerHTML = `
            <strong>Componentes</strong>
            <small>Agrega capas al lienzo o contenedor seleccionado.</small>
        `;

        const grid = document.createElement("div");
        grid.className = "r3-component-library__grid";

        for (const item of listInsertableComponents()) {
            grid.append(this.#renderItem(item));
        }

        this.root.append(header, grid);
    }

    #renderItem(item) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "r3-component-library__item";
        button.dataset.r3ComponentType = item.type;

        const icon = document.createElement("span");
        icon.className = "r3-component-library__icon";
        icon.textContent = item.icon;

        const text = document.createElement("span");
        text.className = "r3-component-library__text";

        const label = document.createElement("strong");
        label.textContent = item.label;

        const description = document.createElement("small");
        description.textContent = item.description;

        text.append(label, description);
        button.append(icon, text);

        button.addEventListener("click", () => {
            const node = insertComponent({
                state: this.state,
                type: item.type,
                selectedNodeId: this.state.selection.nodeId,
                selectedCanvasId: this.state.selection.canvasId,
            });

            this.renderer.update(this.state.document);
            this.canvas.select(node.id);
            this.inspector?.setSelection(node.id);
            this.inspector?.refresh();
            this.onStatus?.(`${item.label} agregado`);
        });

        return button;
    }
}
