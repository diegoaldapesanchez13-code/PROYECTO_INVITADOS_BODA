
import {
    field,
    group,
} from "../controls.js";

export function decorationPanel() {
    return [
        group({
            id: "decoration",
            title: "Decoración",
            description:
                "Recurso transparente colocado libremente.",
            fields: [
                field({
                    key: "objectFit",
                    label: "Ajuste",
                    type: "select",
                    path: "style.objectFit",
                    options: [
                        ["contain", "Contain"],
                        ["cover", "Cover"],
                        ["fill", "Fill"],
                    ],
                }),
                field({
                    key: "flipX",
                    label: "Voltear horizontal",
                    type: "checkbox",
                    path: "style.flipX",
                }),
                field({
                    key: "flipY",
                    label: "Voltear vertical",
                    type: "checkbox",
                    path: "style.flipY",
                }),
                field({
                    key: "blur",
                    label: "Desenfoque",
                    type: "number",
                    path: "style.blur",
                    min: 0,
                    max: 30,
                    step: 0.5,
                    unit: "px",
                }),
                field({
                    key: "boxShadow",
                    label: "Sombra CSS",
                    type: "text",
                    path: "style.boxShadow",
                    placeholder:
                        "0 12px 25px rgba(0,0,0,.18)",
                }),
            ],
        }),
    ];
}
