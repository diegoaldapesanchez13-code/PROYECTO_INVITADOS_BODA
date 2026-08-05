import {
    field,
    group,
} from "../controls.js";

export function countdownPanel() {
    return [
        group({
            id: "countdown-values",
            title: "Vista previa",
            description:
                "Valores temporales para diseñar el componente.",
            fields: [
                field({
                    key: "days",
                    label: "Días",
                    type: "number",
                    path: "content.values.0",
                    min: 0,
                    max: 9999,
                    step: 1,
                }),
                field({
                    key: "hours",
                    label: "Horas",
                    type: "number",
                    path: "content.values.1",
                    min: 0,
                    max: 23,
                    step: 1,
                }),
                field({
                    key: "minutes",
                    label: "Minutos",
                    type: "number",
                    path: "content.values.2",
                    min: 0,
                    max: 59,
                    step: 1,
                }),
                field({
                    key: "seconds",
                    label: "Segundos",
                    type: "number",
                    path: "content.values.3",
                    min: 0,
                    max: 59,
                    step: 1,
                }),
            ],
        }),

        group({
            id: "countdown-style",
            title: "Estilo",
            fields: [
                field({
                    key: "gap",
                    label: "Separación",
                    type: "number",
                    path: "style.gap",
                    min: 0,
                    max: 100,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "color",
                    label: "Color",
                    type: "color",
                    path: "style.color",
                }),
                field({
                    key: "valueSize",
                    label: "Tamaño números",
                    type: "number",
                    path: "style.valueSize",
                    min: 8,
                    max: 200,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "labelSize",
                    label: "Tamaño etiquetas",
                    type: "number",
                    path: "style.labelSize",
                    min: 6,
                    max: 80,
                    step: 1,
                    unit: "px",
                }),
            ],
        }),
    ];
}