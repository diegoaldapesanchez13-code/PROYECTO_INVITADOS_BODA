import {
    COMPONENT_CAPABILITIES,
    NODE_TYPES,
    componentLabel,
    componentSupports,
    getComponentDefinition,
} from "../core/index.js?v=f4-native-v4-freeze";

import {
    autoLayoutPanel,
} from "./panels/auto_layout.js?v=f4-native-v4-freeze";

import {
    constraintsPanel,
} from "./panels/constraints.js?v=f4-native-v4-freeze";


import {
    getPath,
    setPathClone,
    shouldShow,
    valueFromInput,
} from "./controls.js?v=f4-native-v4-freeze";

import {
    generalPanel,
} from "./panels/base.js?v=f4-native-v4-freeze";

import {
    canvasPanel,
} from "./panels/canvas.js?v=f4-native-v4-freeze";

import {
    cardPanel,
} from "./panels/card.js?v=f4-native-v4-freeze";

import {
    textPanel,
} from "./panels/text.js?v=f4-native-v4-freeze";

import {
    imagePanel,
} from "./panels/image.js?v=f4-native-v4-freeze";

import {
    buttonPanel,
} from "./panels/button.js?v=f4-native-v4-freeze";

import {
    countdownPanel,
} from "./panels/countdown.js?v=f4-native-v4-freeze";

import {
    mapPanel,
} from "./panels/map.js?v=f4-native-v4-freeze";

import {
    videoPanel,
} from "./panels/video.js?v=f4-native-v4-freeze";

import {
    rsvpPanel,
} from "./panels/rsvp.js?v=f4-native-v4-freeze";

import {
    separatorPanel,
} from "./panels/separator.js?v=f4-native-v4-freeze";

import {
    iconPanel,
} from "./panels/icon.js?v=f4-native-v4-freeze";

import {
    backgroundPanel,
} from "./panels/background.js?v=f4-native-v4-freeze";

import {
    decorationPanel,
} from "./panels/decoration.js?v=f4-native-v4-freeze";

import {
    interactionPanel,
} from "./panels/interaction.js?v=f4-native-v4-freeze";

export class UniversalInspector {
    constructor(options = {}) {
        const {
            root,
            state,
            renderer,
            canvas,
            onStatus = null,
            onNodeUpdated = null,
            assets = null,
            uploadService = null,
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
        this.assets = assets;
        this.uploadService = uploadService;
        this.selectedNodeId = null;
        this.groupOpenState = new Map();
        this.scrollStateByNode = new Map();

        this.renderEmpty();
    }

    setSelection(nodeId) {
        this.#rememberViewState();
        this.selectedNodeId = nodeId || null;
        this.render();
    }

    refresh() {
        this.#rememberViewState();
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

        if (
            node.type === NODE_TYPES.CANVAS
            && this.state.document.canvases.length <= 1
        ) {
            this.onStatus?.(
                "El documento debe conservar al menos un lienzo."
            );
            return;
        }

        const confirmed = globalThis.confirm
            ? globalThis.confirm(
                node.type === NODE_TYPES.CANVAS
                    ? `¿Eliminar "${node.name}" y todas sus capas?`
                    : `¿Eliminar "${node.name}"?`
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
            assets: this.assets,
            uploadService: this.uploadService,
        };

        this.root.append(header);

        for (const panel of panels) {
            if (!shouldShow(panel, context)) {
                continue;
            }

            if (panel.kind === "group") {
                this.root.append(
                    this.#renderGroup(panel, context)
                );
            }

            if (panel.kind === "action-group") {
                this.root.append(
                    this.#renderActionGroup(panel, context)
                );
            }
        }

        const savedScroll = this.scrollStateByNode.get(node.id) || 0;
        this.root.scrollTop = savedScroll;
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
        if (node.type === NODE_TYPES.CANVAS) {
            return canvasPanel();
        }

        const panelFactories = {
            canvas: canvasPanel,
            card: cardPanel,
            text: textPanel,
            image: imagePanel,
            button: buttonPanel,
            map: mapPanel,
            video: videoPanel,
            rsvp: rsvpPanel,
            countdown: countdownPanel,
            separator: separatorPanel,
            icon: iconPanel,
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

        details.dataset.groupId = definition.id;
        const stateKey = this.#groupStateKey(definition.id);
        details.open = this.groupOpenState.has(stateKey)
            ? this.groupOpenState.get(stateKey)
            : definition.open !== false;
        details.addEventListener("toggle", () => {
            this.groupOpenState.set(stateKey, details.open);
        });

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
                context
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

    #createControl(definition, context) {
        const node = context.node;
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

            const options =
                typeof definition.options
                    === "function"
                    ? definition.options(context)
                    : definition.options;

            for (
                const [
                    value,
                    label,
                ] of options || []
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

        const liveInputTypes = new Set([
            "text",
            "textarea",
            "range",
            "color",
        ]);

        const eventName =
            liveInputTypes.has(definition.type)
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

        const customPatch = typeof definition.onChange === "function"
            ? definition.onChange({
                inspector: this,
                state: this.state,
                assets: this.assets,
                uploadService: this.uploadService,
                current,
                value,
                definition,
            })
            : null;

        const next = customPatch
            ? null
            : setPathClone(
                current,
                definition.path,
                value
            );

        const patch = customPatch
            || topLevelPatch(
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

        // No reconstruir todo el inspector en cada tecla/click.
        // Esto conserva acordeones, foco y posición de scroll.

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

    #rememberViewState() {
        if (!this.selectedNodeId || !this.root) return;
        this.scrollStateByNode.set(
            this.selectedNodeId,
            this.root.scrollTop
        );
        for (const details of this.root.querySelectorAll("details[data-group-id]")) {
            this.groupOpenState.set(
                this.#groupStateKey(details.dataset.groupId),
                details.open
            );
        }
    }

    #groupStateKey(groupId) {
        return `${this.selectedNodeId || "none"}:${groupId}`;
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
