import {
    COMPONENT_CAPABILITIES,
    componentLabel,
    componentSupports,
    getComponentDefinition,
} from "../core/index.js";

import {
    autoLayoutPanel,
} from "./panels/auto_layout.js";

import {
    constraintsPanel,
} from "./panels/constraints.js";


import {
    getPath,
    setPathClone,
    shouldShow,
    valueFromInput,
} from "./controls.js";

import {
    generalPanel,
} from "./panels/base.js";

import {
    sectionPanel,
} from "./panels/section.js";

import {
    cardPanel,
} from "./panels/card.js";

import {
    textPanel,
} from "./panels/text.js";

import {
    imagePanel,
} from "./panels/image.js";

import {
    countdownPanel,
} from "./panels/countdown.js";

import {
    backgroundPanel,
} from "./panels/background.js";

import {
    decorationPanel,
} from "./panels/decoration.js";

import {
    interactionPanel,
} from "./panels/interaction.js";

export class UniversalInspector {
    constructor(options = {}) {
        const {
            root,
            state,
            renderer,
            canvas,
            onStatus = null,
            onNodeUpdated = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "Inspector root debe ser un elemento HTML."
            );
        }

        if (!state || !renderer || !canvas) {
            throw new Error(
                "Inspector requiere state, renderer y canvas."
            );
        }

        this.root = root;
        this.state = state;
        this.renderer = renderer;
        this.canvas = canvas;
        this.onStatus = onStatus;
        this.onNodeUpdated = onNodeUpdated;
        this.selectedNodeId = null;

        this.renderEmpty();
    }

    setSelection(nodeId) {
        this.selectedNodeId =
            nodeId || null;

        this.render();
    }

    refresh() {
        this.render();
    }

    duplicateSelected() {
        if (!this.selectedNodeId) return;

        const clone =
            this.state.duplicateNode(
                this.selectedNodeId
            );

        this.renderer.update(
            this.state.document
        );

        this.canvas.select(clone.id);
        this.setSelection(clone.id);

        this.onNodeUpdated?.({
            type: "duplicate",
            nodeId: clone.id,
        });

        this.onStatus?.(
            `${clone.name} duplicado`
        );
    }

    deleteSelected() {
        if (!this.selectedNodeId) return;

        const node = this.state.getNode(
            this.selectedNodeId
        );

        if (!node) return;

        const confirmed = globalThis.confirm
            ? globalThis.confirm(
                `¿Eliminar "${node.name}"?`
            )
            : true;

        if (!confirmed) return;

        this.state.deleteNode(
            this.selectedNodeId
        );

        this.selectedNodeId = null;
        this.renderer.update(
            this.state.document
        );
        this.canvas.clearSelection();
        this.renderEmpty();

        this.onNodeUpdated?.({
            type: "delete",
            nodeId: node.id,
        });

        this.onStatus?.(
            `${node.name} eliminado`
        );
    }

    render() {
        if (!this.selectedNodeId) {
            this.renderEmpty();
            return;
        }

        const node = this.state.getNode(
            this.selectedNodeId
        );

        if (!node) {
            this.renderEmpty();
            return;
        }

        this.root.replaceChildren();
        this.root.classList.add(
            "r3-inspector"
        );

        const header =
            this.#renderHeader(node);

        const panels =
            this.#panelDefinitions(node);

        const context = {
            node,
            inspector: this,
            state: this.state,
        };

        this.root.append(header);

        for (const panel of panels) {
            if (!shouldShow(panel, context)) {
                continue;
            }

            if (panel.kind === "group") {
                this.root.append(
                    this.#renderGroup(
                        panel,
                        context
                    )
                );
            }

            if (
                panel.kind
                === "action-group"
            ) {
                this.root.append(
                    this.#renderActionGroup(
                        panel,
                        context
                    )
                );
            }
        }
    }

    renderEmpty() {
        this.root.replaceChildren();
        this.root.classList.add(
            "r3-inspector"
        );

        const empty =
            document.createElement("div");

        empty.className =
            "r3-inspector-empty";

        empty.innerHTML = `
            <strong>Ningún elemento seleccionado</strong>
            <p>
                Haz clic sobre un lienzo, una card,
                texto o componente del canvas.
            </p>
        `;

        this.root.append(empty);
    }

    #panelDefinitions(node) {
        const panelFactories = {
            section: sectionPanel,
            card: cardPanel,
            text: textPanel,
            image: imagePanel,
            countdown: countdownPanel,
            background: backgroundPanel,
            decoration: decorationPanel,
        };

        const definition =
            getComponentDefinition(node.type);

        const createSpecific =
            definition?.inspectorPanel
                ? panelFactories[
                    definition.inspectorPanel
                ]
                : null;

        const canAutoLayout =
            componentSupports(
                node.type,
                COMPONENT_CAPABILITIES.AUTO_LAYOUT
            );

        const canUseConstraints =
            componentSupports(
                node.type,
                COMPONENT_CAPABILITIES.CONSTRAINTS
            );

        const canUseInteraction =
            componentSupports(
                node.type,
                COMPONENT_CAPABILITIES.ACTIONABLE
            );

        return [
            ...generalPanel(),
            ...(canAutoLayout ? autoLayoutPanel() : []),
            ...(canUseConstraints ? constraintsPanel() : []),
            ...(createSpecific ? createSpecific() : []),
            ...(canUseInteraction ? interactionPanel() : []),
        ];
    }

    #renderHeader(node) {
        const header =
            document.createElement("header");

        header.className =
            "r3-inspector-header";

        const type =
            document.createElement("span");

        type.className =
            "r3-inspector-header__type";

        type.textContent =
            componentLabel(node.type);

        const title =
            document.createElement("h2");

        title.textContent = node.name;

        const id =
            document.createElement("code");

        id.textContent = node.id;

        header.append(type, title, id);

        return header;
    }

    #renderGroup(definition, context) {
        const details =
            document.createElement("details");

        details.className =
            "r3-inspector-group";

        details.open =
            definition.open !== false;

        const summary =
            document.createElement("summary");

        const title =
            document.createElement("strong");

        title.textContent =
            definition.title;

        summary.append(title);

        if (definition.description) {
            const description =
                document.createElement("small");

            description.textContent =
                definition.description;

            summary.append(description);
        }

        const body =
            document.createElement("div");

        body.className =
            "r3-inspector-group__body";

        for (
            const fieldDefinition
            of definition.fields
        ) {
            if (
                !shouldShow(
                    fieldDefinition,
                    context
                )
            ) {
                continue;
            }

            body.append(
                this.#renderField(
                    fieldDefinition,
                    context
                )
            );
        }

        details.append(summary, body);

        return details;
    }

    #renderField(definition, context) {
        const wrapper =
            document.createElement("label");

        wrapper.className =
            "r3-inspector-field";

        wrapper.dataset.fieldKey =
            definition.key;

        const label =
            document.createElement("span");

        label.className =
            "r3-inspector-field__label";

        label.textContent =
            definition.label;

        wrapper.append(label);

        const control =
            this.#createControl(
                definition,
                context.node
            );

        wrapper.append(control);

        if (definition.unit) {
            const unit =
                document.createElement("span");

            unit.className =
                "r3-inspector-field__unit";

            unit.textContent =
                definition.unit;

            wrapper.append(unit);
        }

        if (definition.help) {
            const help =
                document.createElement("small");

            help.className =
                "r3-inspector-field__help";

            help.textContent =
                definition.help;

            wrapper.append(help);
        }

        return wrapper;
    }

    #createControl(definition, node) {
        let control;

        if (
            definition.type
            === "textarea"
        ) {
            control =
                document.createElement(
                    "textarea"
                );
            control.rows = 3;
        } else if (
            definition.type
            === "select"
        ) {
            control =
                document.createElement(
                    "select"
                );

            for (
                const [
                    value,
                    label,
                ] of definition.options
            ) {
                const option =
                    document.createElement(
                        "option"
                    );

                option.value = value;
                option.textContent = label;
                control.append(option);
            }
        } else {
            control =
                document.createElement(
                    "input"
                );

            control.type =
                definition.type;
        }

        control.className =
            "r3-inspector-control";

        if (definition.min !== null) {
            control.min =
                String(definition.min);
        }

        if (definition.max !== null) {
            control.max =
                String(definition.max);
        }

        if (definition.step !== null) {
            control.step =
                String(definition.step);
        }

        if (definition.placeholder) {
            control.placeholder =
                definition.placeholder;
        }

        const currentValue =
            getPath(
                node,
                definition.path,
                defaultValueForType(
                    definition.type
                )
            );

        if (
            definition.type
            === "checkbox"
        ) {
            control.checked =
                Boolean(currentValue);
        } else if (
            currentValue !== "auto"
        ) {
            control.value =
                currentValue ?? "";
        }

        const eventName =
            definition.type === "text"
            || definition.type
                === "textarea"
            ? "input"
            : "change";

        control.addEventListener(
            eventName,
            () => {
                this.#commitField(
                    definition,
                    control
                );
            }
        );

        return control;
    }

    #commitField(
        definition,
        control
    ) {
        const current =
            this.state.getNode(
                this.selectedNodeId
            );

        if (!current) return;

        const value =
            valueFromInput(
                control,
                definition
            );

        const next =
            setPathClone(
                current,
                definition.path,
                value
            );

        const patch =
            topLevelPatch(
                current,
                next,
                definition.path
            );

        this.state.updateNode(
            current.id,
            patch,
            {
                ignoreLock:
                    definition.path
                    === "locked"
                    || definition.path
                        === "visible"
                    || definition.path
                        === "name",
            }
        );

        this.renderer.update(
            this.state.document
        );

        this.canvas.refreshAfterRender();
        this.canvas.select(
            this.selectedNodeId
        );

        this.render();

        this.onNodeUpdated?.({
            type: "field",
            nodeId: current.id,
            path: definition.path,
            value,
        });

        this.onStatus?.(
            `${current.name}: ${definition.label} actualizado`
        );
    }

    #renderActionGroup(
        definition,
        context
    ) {
        const section =
            document.createElement("section");

        section.className =
            "r3-inspector-actions";

        const title =
            document.createElement("strong");

        title.textContent =
            definition.title;

        const grid =
            document.createElement("div");

        grid.className =
            "r3-inspector-actions__grid";

        for (
            const action
            of definition.actions
        ) {
            if (!shouldShow(action, context)) {
                continue;
            }

            const button =
                document.createElement(
                    "button"
                );

            button.type = "button";
            button.textContent =
                action.label;

            button.dataset.tone =
                action.tone;

            button.addEventListener(
                "click",
                () => action.handler(
                    context
                )
            );

            grid.append(button);
        }

        section.append(title, grid);

        return section;
    }
}

function topLevelPatch(
    current,
    next,
    path
) {
    const topKey =
        String(path).split(".")[0];

    return {
        [topKey]: next[topKey],
    };
}

function defaultValueForType(type) {
    if (type === "checkbox") {
        return false;
    }

    if (
        type === "number"
        || type === "range"
    ) {
        return 0;
    }

    return "";
}
