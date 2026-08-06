import {
    COORDINATE_SPACES,
    LAYOUT_MODES,
    NODE_TYPES,
    isContainerComponent,
} from "../core/index.js";

export function insertComponent(options = {}) {
    const {
        state,
        type,
        selectedNodeId = state?.selection?.nodeId || null,
    } = options;

    if (!state) {
        throw new Error("insertComponent requiere state.");
    }

    const target = resolveInsertionTarget(state, selectedNodeId);

    if (!target) {
        throw new Error(
            "El documento necesita al menos un lienzo para insertar componentes."
        );
    }

    const sectionId = target.type === NODE_TYPES.SECTION
        ? target.id
        : target.sectionId;

    const siblingCount = state.getChildren(target.id).length;
    const offset = Math.min(siblingCount * 2.5, 20);
    const zIndex = nextLayerLevel(state, target.id);

    const common = {
        parentId: target.id,
        sectionId,
        layoutMode: LAYOUT_MODES.ABSOLUTE,
        coordinateSpace: target.type === NODE_TYPES.SECTION
            ? COORDINATE_SPACES.SECTION
            : COORDINATE_SPACES.PARENT,
        x: 50,
        y: 32 + offset,
        zIndex,
    };

    if (type === NODE_TYPES.COUNTDOWN) {
        return createCompositeCountdown(state, common);
    }

    const definition = createDefinition(type, common);

    if (!definition) {
        throw new Error(`Componente no insertable: ${type}`);
    }

    return state.createNode(type, definition);
}

export function resolveInsertionTarget(state, selectedNodeId = null) {
    const selected = selectedNodeId
        ? state.getNode(selectedNodeId)
        : null;

    if (selected && isContainerComponent(selected.type)) {
        return selected;
    }

    if (selected?.sectionId) {
        const section = state.getNode(selected.sectionId);
        if (section) return section;
    }

    return [...state.document.sections]
        .sort((a, b) => a.order - b.order)[0]
        || null;
}

function createDefinition(type, common) {
    switch (type) {
        case NODE_TYPES.TEXT:
            return {
                ...common,
                name: "Texto",
                width: 72,
                height: 12,
                content: {
                    text: "Escribe aquí",
                    tag: "p",
                },
                style: {
                    color: "#2f342d",
                    fontFamily: "Georgia, serif",
                    fontSize: 24,
                    fontWeight: 400,
                    textAlign: "center",
                    lineHeight: 1.25,
                    letterSpacing: 0,
                },
            };

        case NODE_TYPES.BUTTON:
            return {
                ...common,
                name: "Botón",
                width: 46,
                height: 8,
                content: {
                    label: "Botón",
                    href: "#",
                },
                style: {
                    color: "#ffffff",
                    backgroundColor: "#526043",
                    borderColor: "#526043",
                    borderWidth: 0,
                    borderRadius: 999,
                    boxShadow: "0 10px 24px rgba(45, 55, 39, .20)",
                    fontFamily: "Arial, sans-serif",
                    fontSize: 14,
                    fontWeight: 700,
                    textAlign: "center",
                    paddingX: 22,
                    paddingY: 11,
                },
            };

        case NODE_TYPES.CARD:
            return {
                ...common,
                name: "Card",
                width: 84,
                height: 34,
                content: {},
                style: {
                    direction: "column",
                    align: "stretch",
                    justify: "start",
                    gap: 12,
                    paddingX: 20,
                    paddingY: 20,
                    backgroundColor: "#ffffff",
                    borderColor: "#ded8cd",
                    borderWidth: 1,
                    borderRadius: 24,
                    boxShadow: "0 18px 45px rgba(31, 39, 29, .14)",
                },
            };

        case NODE_TYPES.CONTAINER:
            return {
                ...common,
                name: "Contenedor",
                width: 84,
                height: 34,
                content: {},
                style: {
                    direction: "column",
                    align: "stretch",
                    justify: "start",
                    gap: 10,
                    paddingX: 0,
                    paddingY: 0,
                    backgroundColor: "transparent",
                    borderWidth: 0,
                    borderRadius: 0,
                    boxShadow: "none",
                },
            };

        case NODE_TYPES.MAP:
            return {
                ...common,
                name: "Google Maps",
                width: 84,
                height: 34,
                content: {
                    source: "21.1225,-101.6834",
                    zoom: 15,
                    title: "Ubicación del evento",
                    loading: "lazy",
                },
                style: {
                    backgroundColor: "#ece9e1",
                    borderColor: "#d7d2c8",
                    borderWidth: 1,
                    borderRadius: 18,
                    boxShadow: "0 12px 30px rgba(35, 40, 31, .14)",
                    overflow: "hidden",
                },
            };

        case NODE_TYPES.COUNTDOWN:
            return countdownParentDefinition(common);

        case NODE_TYPES.SEPARATOR:
            return {
                ...common,
                name: "Separador",
                width: 72,
                height: 2,
                content: {},
                style: {
                    orientation: "horizontal",
                    color: "#526043",
                    borderWidth: 1,
                    borderStyle: "solid",
                    borderRadius: 999,
                },
            };

        case NODE_TYPES.ICON:
            return {
                ...common,
                name: "Icono",
                width: 14,
                height: 10,
                content: {
                    value: "✦",
                },
                style: {
                    color: "#526043",
                    fontFamily: "Georgia, serif",
                    fontSize: 34,
                    fontWeight: 400,
                    textAlign: "center",
                    lineHeight: 1,
                },
            };

        default:
            return null;
    }
}

function createCompositeCountdown(state, common) {
    return state.transaction("component:countdown:create", () => {
        const parent = state.createNode(
            NODE_TYPES.COUNTDOWN,
            countdownParentDefinition(common)
        );

        const units = [
            ["days", "Días", 120, 12.5],
            ["hours", "Horas", 12, 37.5],
            ["minutes", "Minutos", 34, 62.5],
            ["seconds", "Segundos", 56, 87.5],
        ];

        for (const [unit, label, previewValue, x] of units) {
            const item = state.createNode(NODE_TYPES.CARD, {
                parentId: parent.id,
                sectionId: parent.sectionId,
                name: label,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x,
                y: 50,
                width: 23,
                height: 88,
                zIndex: 1,
                style: {
                    paddingX: 4,
                    paddingY: 4,
                    backgroundColor: "#ffffff",
                    borderColor: "#dfe5db",
                    borderWidth: 1,
                    borderRadius: 16,
                    boxShadow: "none",
                    overflow: "visible",
                },
                content: { countdownUnit: unit },
            });

            state.createNode(NODE_TYPES.TEXT, {
                parentId: item.id,
                sectionId: parent.sectionId,
                name: `${label} · Número`,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x: 50,
                y: 38,
                width: 92,
                height: 34,
                zIndex: 2,
                content: {
                    text: String(previewValue),
                    tag: "span",
                    binding: {
                        source: "COUNTDOWN",
                        unit,
                        role: "value",
                    },
                },
                style: {
                    color: "#2f342d",
                    fontFamily: "'Playfair Display', serif",
                    fontSize: 30,
                    fontWeight: 700,
                    textAlign: "center",
                    lineHeight: 1,
                    letterSpacing: 0,
                },
            });

            state.createNode(NODE_TYPES.TEXT, {
                parentId: item.id,
                sectionId: parent.sectionId,
                name: `${label} · Etiqueta`,
                layoutMode: LAYOUT_MODES.ABSOLUTE,
                coordinateSpace: COORDINATE_SPACES.PARENT,
                x: 50,
                y: 72,
                width: 94,
                height: 22,
                zIndex: 3,
                content: {
                    text: label,
                    tag: "span",
                    binding: {
                        source: "COUNTDOWN",
                        unit,
                        role: "label",
                    },
                },
                style: {
                    color: "#777971",
                    fontFamily: "Montserrat, sans-serif",
                    fontSize: 10,
                    fontWeight: 600,
                    textAlign: "center",
                    lineHeight: 1.15,
                    letterSpacing: 1,
                    textTransform: "uppercase",
                },
            });
        }

        return state.getNode(parent.id);
    });
}

function countdownParentDefinition(common) {
    return {
        ...common,
        name: "Cuenta regresiva",
        width: 88,
        height: 18,
        content: {
            targetDate: "",
            values: [120, 12, 34, 56],
            labels: ["Días", "Horas", "Minutos", "Segundos"],
            compositeVersion: 1,
        },
        style: {
            valueColor: "#526043",
            labelColor: "#777971",
            valueFontFamily: "Georgia, serif",
            labelFontFamily: "Arial, sans-serif",
            itemBorderRadius: 16,
            backgroundColor: "transparent",
            borderWidth: 0,
            borderRadius: 0,
            boxShadow: "none",
            overflow: "visible",
        },
    };
}

function nextLayerLevel(state, parentId) {
    const levels = state.getChildren(parentId)
        .map((node) => Number(node.zIndex || 0));

    return Math.max(0, ...levels) + 1;
}
