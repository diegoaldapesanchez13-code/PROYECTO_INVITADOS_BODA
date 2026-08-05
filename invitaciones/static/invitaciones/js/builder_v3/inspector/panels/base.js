import {
    action,
    actionGroup,
    field,
    group,
} from "../controls.js";

export function generalPanel() {
    return [
        group({
            id: "general",
            title: "General",
            description:
                "Identidad y estado del nodo seleccionado.",
            fields: [
                field({
                    key: "name",
                    label: "Nombre",
                    type: "text",
                }),
                field({
                    key: "visible",
                    label: "Visible",
                    type: "checkbox",
                }),
                field({
                    key: "locked",
                    label: "Bloqueado",
                    type: "checkbox",
                }),
                field({
                    key: "layoutMode",
                    label: "Modo de layout",
                    type: "select",
                    visibleWhen: ({ node }) =>
                        ![
                            "SECTION",
                            "BACKGROUND",
                        ].includes(node.type),
                    options: [
                        ["FLOW", "Flow"],
                        ["ABSOLUTE", "Absolute"],
                        ["LAYER", "Layer"],
                    ],
                    help:
                        "SECTION permanece en Flow y BACKGROUND permanece en Layer.",
                }),
            ],
        }),

        group({
            id: "position",
            title: "Posición y tamaño",
            description:
                "Disponible para nodos libres en Absolute o Layer.",
            visibleWhen: ({ node }) =>
                ![
                    "SECTION",
                    "BACKGROUND",
                ].includes(node.type)
                && [
                    "ABSOLUTE",
                    "LAYER",
                ].includes(node.layoutMode),
            fields: [
                field({
                    key: "x",
                    label: "X",
                    type: "number",
                    min: -100,
                    max: 200,
                    step: 0.1,
                    unit: "%",
                }),
                field({
                    key: "y",
                    label: "Y",
                    type: "number",
                    min: -100,
                    max: 200,
                    step: 0.1,
                    unit: "%",
                }),
                field({
                    key: "width",
                    label: "Ancho",
                    type: "number",
                    min: 1,
                    max: 200,
                    step: 0.1,
                    unit: "%",
                }),
                field({
                    key: "height",
                    label: "Alto",
                    type: "number",
                    min: 1,
                    max: 200,
                    step: 0.1,
                    unit: "%",
                }),
                field({
                    key: "rotation",
                    label: "Rotación",
                    type: "number",
                    min: -360,
                    max: 360,
                    step: 1,
                    unit: "°",
                }),
                field({
                    key: "scale",
                    label: "Escala",
                    type: "number",
                    min: 0.1,
                    max: 5,
                    step: 0.05,
                    unit: "x",
                }),

            ],
        }),

        group({
            id: "appearance",
            title: "Apariencia",
            fields: [
                field({
                    key: "opacity",
                    label: "Opacidad",
                    type: "number",
                    min: 0,
                    max: 1,
                    step: 0.05,
                }),
            ],
        }),

        actionGroup({
            id: "actions",
            title: "Acciones",
            actions: [
                action({
                    id: "duplicate",
                    label: "Duplicar",
                    handler: ({ inspector }) =>
                        inspector.duplicateSelected(),
                }),
                action({
                    id: "delete",
                    label: "Eliminar",
                    tone: "danger",
                    visibleWhen: ({ node }) =>
                        node.type !== "SECTION",
                    handler: ({ inspector }) =>
                        inspector.deleteSelected(),
                }),
            ],
        }),
    ];
}
