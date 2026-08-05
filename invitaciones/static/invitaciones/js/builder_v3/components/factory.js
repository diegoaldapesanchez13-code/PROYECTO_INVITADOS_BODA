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

    const target = resolveInsertionTarget(
        state,
        selectedNodeId
    );

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

    if (type === NODE_TYPES.TEXT) {
        return state.createNode(
            NODE_TYPES.TEXT,
            {
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
            }
        );
    }

    if (type === NODE_TYPES.BUTTON) {
        return state.createNode(
            NODE_TYPES.BUTTON,
            {
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
            }
        );
    }

    throw new Error(`Componente no insertable en esta fase: ${type}`);
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

function nextLayerLevel(state, parentId) {
    const levels = state.getChildren(parentId)
        .map((node) => Number(node.zIndex || 0));

    return Math.max(0, ...levels) + 1;
}
