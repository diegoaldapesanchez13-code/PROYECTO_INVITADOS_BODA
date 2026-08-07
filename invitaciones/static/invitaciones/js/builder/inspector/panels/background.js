
import {
    field,
    group,
} from "../controls.js";

export function backgroundPanel() {
    return [
        group({
            id: "background-source",
            title: "Fondo",
            description:
                "El recurso se selecciona desde Design Studio.",
            fields: [
                field({
                    key: "assetId",
                    label: "Asset ID",
                    type: "text",
                    path: "content.assetId",
                    help:
                        "Selecciona otro fondo desde el panel izquierdo.",
                }),
                field({
                    key: "fit",
                    label: "Ajuste",
                    type: "select",
                    path: "style.fit",
                    options: [
                        ["cover", "Cover"],
                        ["contain", "Contain"],
                        ["original", "Original"],
                    ],
                }),
                field({
                    key: "positionX",
                    label: "Posición X",
                    type: "number",
                    path: "style.positionX",
                    min: 0,
                    max: 100,
                    step: 1,
                    unit: "%",
                }),
                field({
                    key: "positionY",
                    label: "Posición Y",
                    type: "number",
                    path: "style.positionY",
                    min: 0,
                    max: 100,
                    step: 1,
                    unit: "%",
                }),
                field({
                    key: "zoom",
                    label: "Zoom",
                    type: "number",
                    path: "style.zoom",
                    min: 0.25,
                    max: 4,
                    step: 0.05,
                    unit: "x",
                }),
            ],
        }),

        group({
            id: "background-effects",
            title: "Efectos",
            fields: [
                field({
                    key: "brightness",
                    label: "Brillo",
                    type: "number",
                    path: "style.brightness",
                    min: 0,
                    max: 2,
                    step: 0.05,
                }),
                field({
                    key: "contrast",
                    label: "Contraste",
                    type: "number",
                    path: "style.contrast",
                    min: 0,
                    max: 2,
                    step: 0.05,
                }),
                field({
                    key: "saturation",
                    label: "Saturación",
                    type: "number",
                    path: "style.saturation",
                    min: 0,
                    max: 2,
                    step: 0.05,
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
            ],
        }),
    ];
}
