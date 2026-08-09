import {
    field,
    group,
} from "../controls.js";

export function canvasPanel() {
    return [
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
                field({
                    key: "overflow",
                    label: "Contenido excedente",
                    type: "select",
                    path: "style.overflow",
                    options: [
                        ["hidden", "Ocultar"],
                        ["visible", "Mostrar"],
                    ],
                }),
            ],
        }),
    ];
}
