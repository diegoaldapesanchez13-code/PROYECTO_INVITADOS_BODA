import { field, group } from "../controls.js";

export function rsvpPanel() {
    return [
        group({
            id: "rsvp-content",
            title: "RSVP",
            description: "En el editor se muestran datos de ejemplo. En publicación se usan el UUID y los datos reales del SaaS.",
            fields: [
                field({ key: "rsvpTitle", label: "Título", path: "content.title", type: "text" }),
                field({ key: "rsvpDescription", label: "Descripción", path: "content.description", type: "textarea" }),
                field({ key: "rsvpAcceptLabel", label: "Texto confirmar", path: "content.acceptLabel", type: "text" }),
                field({ key: "rsvpDeclineLabel", label: "Texto rechazar", path: "content.declineLabel", type: "text" }),
                field({ key: "rsvpSubmitLabel", label: "Texto enviar", path: "content.submitLabel", type: "text" }),
                field({ key: "rsvpShowGroup", label: "Mostrar nombre del grupo", path: "content.showGroupName", type: "checkbox" }),
                field({ key: "rsvpShowLimit", label: "Mostrar cantidad de pases", path: "content.showGuestLimit", type: "checkbox" }),
                field({ key: "rsvpShowComment", label: "Permitir comentario", path: "content.showComment", type: "checkbox" }),
            ],
        }),
        group({
            id: "rsvp-preview",
            title: "Datos de ejemplo",
            fields: [
                field({ key: "rsvpPreviewGroup", label: "Nombre del grupo", path: "content.preview.groupName", type: "text" }),
                field({ key: "rsvpPreviewMax", label: "Pases máximos", path: "content.preview.maxGuests", type: "number", min: 1, max: 50, step: 1 }),
                field({ key: "rsvpPreviewConfirmed", label: "Asistentes de ejemplo", path: "content.preview.confirmedGuests", type: "number", min: 0, max: 50, step: 1 }),
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
