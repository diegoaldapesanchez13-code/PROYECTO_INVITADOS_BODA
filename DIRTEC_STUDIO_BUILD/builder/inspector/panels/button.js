import {
    field,
    group,
} from "../controls.js";

export function buttonPanel() {
    return [
        group({
            id: "button-content",
            title: "Botón",
            fields: [
                field({
                    key: "label",
                    label: "Texto",
                    type: "text",
                    path: "content.label",
                }),
                field({
                    key: "fontFamily",
                    label: "Fuente",
                    type: "text",
                    path: "style.fontFamily",
                    placeholder: "Arial, sans-serif",
                }),
                field({
                    key: "fontSize",
                    label: "Tamaño",
                    type: "number",
                    path: "style.fontSize",
                    min: 6,
                    max: 160,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "fontWeight",
                    label: "Peso",
                    type: "number",
                    path: "style.fontWeight",
                    min: 100,
                    max: 900,
                    step: 100,
                }),
                field({
                    key: "color",
                    label: "Color de texto",
                    type: "color",
                    path: "style.color",
                }),
            ],
        }),
        group({
            id: "button-appearance",
            title: "Apariencia",
            fields: [
                field({
                    key: "backgroundColor",
                    label: "Fondo",
                    type: "color",
                    path: "style.backgroundColor",
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
                    key: "borderRadius",
                    label: "Radio",
                    type: "number",
                    path: "style.borderRadius",
                    min: 0,
                    max: 999,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "boxShadow",
                    label: "Sombra CSS",
                    type: "text",
                    path: "style.boxShadow",
                }),
            ],
        }),
    ];
}
