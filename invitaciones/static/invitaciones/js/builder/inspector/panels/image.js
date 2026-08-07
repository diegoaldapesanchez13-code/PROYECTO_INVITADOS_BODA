import {
    field,
    group,
} from "../controls.js";

export function imagePanel() {
    return [
        group({
            id: "image-source",
            title: "Imagen",
            fields: [
                field({
                    key: "src",
                    label: "URL",
                    type: "text",
                    path: "content.src",
                    placeholder:
                        "https://...",
                }),
                field({
                    key: "alt",
                    label: "Texto alternativo",
                    type: "text",
                    path: "content.alt",
                }),
                field({
                    key: "objectFit",
                    label: "Ajuste",
                    type: "select",
                    path: "style.objectFit",
                    options: [
                        ["cover", "Cover"],
                        ["contain", "Contain"],
                        ["fill", "Fill"],
                        ["none", "Original"],
                    ],
                }),
            ],
        }),

        group({
            id: "image-appearance",
            title: "Apariencia",
            fields: [
                field({
                    key: "borderRadius",
                    label: "Radio",
                    type: "number",
                    path: "style.borderRadius",
                    min: 0,
                    max: 300,
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