import { field, group } from "../controls.js";

export function constraintsPanel() {
    return [
        group({
            id: "constraints",
            title: "Constraints",
            description: "Respuesta del nodo cuando cambia su contenedor.",
            fields: [
                field({
                    key: "horizontal",
                    label: "Horizontal",
                    type: "select",
                    path: "constraints.horizontal",
                    options: [
                        ["LEFT", "Izquierda"],
                        ["CENTER_X", "Centro"],
                        ["RIGHT", "Derecha"],
                        ["SCALE_X", "Escalar"],
                    ],
                }),
                field({
                    key: "vertical",
                    label: "Vertical",
                    type: "select",
                    path: "constraints.vertical",
                    options: [
                        ["TOP", "Arriba"],
                        ["CENTER_Y", "Centro"],
                        ["BOTTOM", "Abajo"],
                        ["SCALE_Y", "Escalar"],
                    ],
                }),
                field({
                    key: "keepAspect",
                    label: "Mantener proporción",
                    type: "checkbox",
                    path: "constraints.keepAspect",
                }),
            ],
        }),
    ];
}