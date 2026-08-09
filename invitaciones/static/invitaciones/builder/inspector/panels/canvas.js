import {
    action,
    actionGroup,
    field,
    group,
} from "../controls.js";

export function canvasPanel() {
    return [
        group({
            id: "canvas-general",
            title: "General",
            description:
                "Identidad del lienzo seleccionado.",
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
            ],
        }),

        group({
            id: "canvas-size",
            title: "Lienzo móvil",
            description:
                "El ancho es fijo para móvil. Ajusta únicamente la altura.",
            fields: [
                field({
                    key: "height",
                    label: "Altura",
                    type: "number",
                    min: 240,
                    max: 6000,
                    step: 10,
                    unit: "px",
                    help:
                        "Los lienzos se apilan verticalmente y forman el scroll de la invitación.",
                }),
            ],
        }),

        actionGroup({
            id: "canvas-actions",
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
                    visibleWhen: ({ state }) =>
                        state.document.canvases.length > 1,
                    handler: ({ inspector }) =>
                        inspector.deleteSelected(),
                }),
            ],
        }),
    ];
}
