import {
    field,
    group,
} from "../controls.js";

export function textPanel() {
    return [
        group({
            id: "text-content",
            title: "Contenido",
            fields: [
                field({
                    key: "text",
                    label: "Texto",
                    type: "textarea",
                    path: "content.text",
                }),
                field({
                    key: "tag",
                    label: "Etiqueta",
                    type: "select",
                    path: "content.tag",
                    options: [
                        ["p", "Párrafo"],
                        ["h1", "Título H1"],
                        ["h2", "Título H2"],
                        ["h3", "Título H3"],
                        ["span", "Span"],
                    ],
                }),
            ],
        }),

        group({
            id: "typography",
            title: "Tipografía",
            fields: [
                field({
                    key: "fontFamily",
                    label: "Fuente",
                    type: "text",
                    path: "style.fontFamily",
                    placeholder:
                        "Georgia, serif",
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
                field({
                    key: "textAlign",
                    label: "Alineación",
                    type: "select",
                    path: "style.textAlign",
                    options: [
                        ["left", "Izquierda"],
                        ["center", "Centro"],
                        ["right", "Derecha"],
                    ],
                }),
                field({
                    key: "lineHeight",
                    label: "Interlineado",
                    type: "number",
                    path: "style.lineHeight",
                    min: 0.5,
                    max: 4,
                    step: 0.05,
                }),
                field({
                    key: "letterSpacing",
                    label: "Espaciado",
                    type: "number",
                    path: "style.letterSpacing",
                    min: -10,
                    max: 50,
                    step: 0.1,
                    unit: "px",
                }),
            ],
        }),
    ];
}