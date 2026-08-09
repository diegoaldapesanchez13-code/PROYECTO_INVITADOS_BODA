import {
    field,
    group,
} from "../controls.js";

export function cardPanel() {
    return [
        group({
            id: "card-layout",
            title: "Layout",
            fields: [
                field({
                    key: "direction",
                    label: "Dirección",
                    type: "select",
                    path: "style.direction",
                    options: [
                        ["column", "Vertical"],
                        ["row", "Horizontal"],
                    ],
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
            ],
        }),

        group({
            id: "card-appearance",
            title: "Tarjeta",
            fields: [
                field({
                    key: "backgroundColor",
                    label: "Fondo",
                    type: "color",
                    path: "style.backgroundColor",
                }),
                field({
                    key: "borderRadius",
                    label: "Radio",
                    type: "number",
                    path: "style.borderRadius",
                    min: 0,
                    max: 200,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "borderWidth",
                    label: "Borde",
                    type: "number",
                    path: "style.borderWidth",
                    min: 0,
                    max: 30,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "borderColor",
                    label: "Color del borde",
                    type: "color",
                    path: "style.borderColor",
                }),
                field({
                    key: "boxShadow",
                    label: "Sombra CSS",
                    type: "text",
                    path: "style.boxShadow",
                    placeholder:
                        "0 18px 45px rgba(0,0,0,.18)",
                }),
            ],
        }),
    ];
}