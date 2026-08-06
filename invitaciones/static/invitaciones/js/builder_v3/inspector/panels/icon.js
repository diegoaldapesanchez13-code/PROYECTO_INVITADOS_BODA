import { field, group } from "../controls.js";

export function iconPanel() {
    return [
        group({
            id: "icon-content",
            title: "Icono",
            description: "Puedes usar un símbolo Unicode, emoji o carácter de una fuente de iconos.",
            fields: [
                field({
                    key: "value",
                    label: "Símbolo",
                    type: "text",
                    path: "content.value",
                }),
                field({
                    key: "fontFamily",
                    label: "Tipografía",
                    type: "text",
                    path: "style.fontFamily",
                }),
                field({
                    key: "fontSize",
                    label: "Tamaño",
                    type: "number",
                    path: "style.fontSize",
                    min: 6,
                    max: 300,
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
                    label: "Color",
                    type: "color",
                    path: "style.color",
                }),
            ],
        }),
    ];
}
