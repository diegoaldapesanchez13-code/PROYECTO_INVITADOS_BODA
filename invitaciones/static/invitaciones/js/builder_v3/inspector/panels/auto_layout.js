import { field, group } from "../controls.js";

export function autoLayoutPanel() {
    return [
        group({
            id: "auto-layout",
            title: "Auto Layout",
            description: "Organiza automáticamente los hijos FLOW.",
            fields: [
                field({
                    key: "direction",
                    label: "Dirección",
                    type: "select",
                    path: "style.direction",
                    options: [["column", "Vertical"], ["row", "Horizontal"]],
                }),
                field({
                    key: "wrap",
                    label: "Permitir wrap",
                    type: "checkbox",
                    path: "style.wrap",
                }),
                field({
                    key: "align",
                    label: "Alineación",
                    type: "select",
                    path: "style.align",
                    options: [
                        ["start", "Inicio"],
                        ["center", "Centro"],
                        ["end", "Final"],
                        ["stretch", "Estirar"],
                    ],
                }),
                field({
                    key: "justify",
                    label: "Distribución",
                    type: "select",
                    path: "style.justify",
                    options: [
                        ["start", "Inicio"],
                        ["center", "Centro"],
                        ["end", "Final"],
                        ["space-between", "Separar"],
                    ],
                }),
                field({
                    key: "gap",
                    label: "Separación",
                    type: "number",
                    path: "style.gap",
                    min: 0,
                    max: 200,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "paddingX",
                    label: "Padding horizontal",
                    type: "number",
                    path: "style.paddingX",
                    min: 0,
                    max: 300,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "paddingY",
                    label: "Padding vertical",
                    type: "number",
                    path: "style.paddingY",
                    min: 0,
                    max: 300,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "sizingX",
                    label: "Ancho",
                    type: "select",
                    path: "style.sizingX",
                    options: [["fixed", "Fijo"], ["fill", "Fill"], ["hug", "Hug"]],
                }),
                field({
                    key: "sizingY",
                    label: "Alto",
                    type: "select",
                    path: "style.sizingY",
                    options: [["fixed", "Fijo"], ["fill", "Fill"], ["hug", "Hug"]],
                }),
            ],
        }),
    ];
}