import { field, group } from "../controls.js";

export function rsvpPanel() {
    return [
        group({
            id: "rsvp-content",
            title: "RSVP individual",
            description:
                "En publicación se cargan las personas reales de la invitación. Cada persona responde Sí o No de forma independiente.",
            fields: [
                field({ key: "rsvpTitle", label: "Título", path: "content.title", type: "text" }),
                field({ key: "rsvpDescription", label: "Descripción", path: "content.description", type: "textarea" }),
                field({ key: "rsvpAcceptLabel", label: "Texto confirmar", path: "content.acceptLabel", type: "text" }),
                field({ key: "rsvpDeclineLabel", label: "Texto rechazar", path: "content.declineLabel", type: "text" }),
                field({ key: "rsvpSubmitLabel", label: "Texto guardar", path: "content.submitLabel", type: "text" }),
                field({ key: "rsvpShowGroup", label: "Mostrar nombre de invitación", path: "content.showGroupName", type: "checkbox" }),
                field({ key: "rsvpShowPersonType", label: "Mostrar Adulto / Niño", path: "content.showPersonType", type: "checkbox" }),
                field({ key: "rsvpShowMenu", label: "Mostrar menú asignado", path: "content.showMenu", type: "checkbox", help: "Solo informativo. El invitado no puede cambiar este valor." }),
                field({
                    key: "rsvpDensity",
                    label: "Densidad",
                    path: "content.density",
                    type: "select",
                    options: [
                        ["AUTO", "Automática"],
                        ["COMPACT", "Compacta"],
                        ["COMFORTABLE", "Cómoda"],
                    ],
                    help: "Automática usa una vista más compacta cuando hay varias personas.",
                }),
            ],
        }),
        group({
            id: "rsvp-preview",
            title: "Vista previa",
            description:
                "El editor usa un roster de personas de ejemplo. Los nombres y respuestas reales llegan desde Django al publicar.",
            fields: [
                field({
                    key: "rsvpPreviewGroup",
                    label: "Nombre del grupo de ejemplo",
                    path: "content.preview.groupName",
                    type: "text",
                }),
            ],
        }),
        group({
            id: "rsvp-appearance",
            title: "Apariencia",
            fields: [
                field({ key: "rsvpBackground", label: "Fondo", path: "style.backgroundColor", type: "color" }),
                field({ key: "rsvpTextColor", label: "Texto", path: "style.color", type: "color" }),
                field({ key: "rsvpAccent", label: "Color principal", path: "style.accentColor", type: "color" }),
                field({ key: "rsvpRadius", label: "Radio", path: "style.borderRadius", type: "number", min: 0, max: 300, step: 1, unit: "px" }),
                field({ key: "rsvpBorderWidth", label: "Borde", path: "style.borderWidth", type: "number", min: 0, max: 20, step: 1, unit: "px" }),
                field({ key: "rsvpBorderColor", label: "Color del borde", path: "style.borderColor", type: "color" }),
                field({ key: "rsvpShadow", label: "Sombra CSS", path: "style.boxShadow", type: "text" }),
            ],
        }),
    ];
}
