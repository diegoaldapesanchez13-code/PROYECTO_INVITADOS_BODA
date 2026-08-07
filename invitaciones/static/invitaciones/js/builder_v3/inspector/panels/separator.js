import { field, group } from "../controls.js";

export function separatorPanel() {
    return [
        group({
            id: "separator-style",
            title: "Separador",
            fields: [
                field({
                    key: "orientation",
                    label: "Orientación",
                    type: "select",
                    path: "style.orientation",
                    options: [
                        ["horizontal", "Horizontal"],
                        ["vertical", "Vertical"],
                    ],
                }),
                field({
                    key: "color",
                    label: "Color",
                    type: "color",
                    path: "style.color",
                }),
                field({
                    key: "borderWidth",
                    label: "Grosor",
                    type: "number",
                    path: "style.borderWidth",
                    min: 1,
                    max: 30,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "borderStyle",
                    label: "Estilo",
                    type: "select",
                    path: "style.borderStyle",
                    options: [
                        ["solid", "Sólido"],
                        ["dashed", "Guiones"],
                        ["dotted", "Puntos"],
                        ["double", "Doble"],
                    ],
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
            ],
        }),
    ];
}
