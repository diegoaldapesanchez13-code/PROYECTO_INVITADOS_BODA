import {
    field,
    group,
} from "../controls.js";

export function mapPanel() {
    return [
        group({
            id: "map-content",
            title: "Google Maps",
            description: "Usa coordenadas, una dirección, una URL de Maps o el código iframe de Google.",
            fields: [
                field({
                    key: "mapSource",
                    label: "Ubicación o enlace",
                    type: "textarea",
                    path: "content.source",
                    placeholder: "21.1225,-101.6834 o https://www.google.com/maps/...",
                    help: "Los enlaces cortos maps.app.goo.gl abren Maps, pero no pueden mostrarse dentro del iframe sin resolver primero su destino.",
                }),
                field({
                    key: "mapZoom",
                    label: "Zoom del mapa",
                    type: "range",
                    path: "content.zoom",
                    min: 1,
                    max: 21,
                    step: 1,
                }),
                field({
                    key: "mapTitle",
                    label: "Título accesible",
                    type: "text",
                    path: "content.title",
                    placeholder: "Ubicación del evento",
                }),
                field({
                    key: "mapLoading",
                    label: "Carga",
                    type: "select",
                    path: "content.loading",
                    options: [
                        ["lazy", "Diferida"],
                        ["eager", "Inmediata"],
                    ],
                }),
            ],
        }),
        group({
            id: "map-appearance",
            title: "Apariencia",
            fields: [
                field({
                    key: "mapRadius",
                    label: "Radio",
                    type: "number",
                    path: "style.borderRadius",
                    min: 0,
                    max: 300,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "mapBorderWidth",
                    label: "Grosor del borde",
                    type: "number",
                    path: "style.borderWidth",
                    min: 0,
                    max: 30,
                    step: 1,
                    unit: "px",
                }),
                field({
                    key: "mapBorderColor",
                    label: "Color del borde",
                    type: "color",
                    path: "style.borderColor",
                }),
                field({
                    key: "mapBackground",
                    label: "Fondo de carga",
                    type: "color",
                    path: "style.backgroundColor",
                }),
                field({
                    key: "mapShadow",
                    label: "Sombra CSS",
                    type: "text",
                    path: "style.boxShadow",
                    placeholder: "0 12px 32px rgba(0,0,0,.18)",
                }),
            ],
        }),
    ];
}
