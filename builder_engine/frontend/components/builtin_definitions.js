import {
    BUILTIN_COMPONENT_TYPES as T,
    COMPONENT_CAPABILITIES as C,
} from "./constants.js";

const transform = [C.CONSTRAINTS, C.TRANSFORM];

export function builtinComponentDefinitions() {
    return [
        component(T.TEXT, "Texto", "T", "p", "text", transform.concat(C.ACTIONABLE, C.DYNAMIC_DATA), {
            content: { text: "Escribe aquí", tag: "p" },
            style: { fontSize: 24, fontWeight: 400, textAlign: "center", lineHeight: 1.25 },
        }),
        component(T.IMAGE, "Imagen", "IM", "img", "image", transform.concat(C.MEDIA, C.ACTIONABLE), {
            content: { assetId: null, alt: "" },
            style: { objectFit: "cover" },
        }),
        component(T.BUTTON, "Botón", "BT", "a", "button", transform.concat(C.ACTIONABLE), {
            content: { label: "Botón", href: "#" },
            style: { borderRadius: 999, textAlign: "center" },
        }),
        component(T.CARD, "Card", "CD", "div", "card", transform.concat(C.CONTAINER, C.AUTO_LAYOUT, C.ACTIONABLE), {
            style: { direction: "column", gap: 12, borderRadius: 24 },
        }),
        component(T.CONTAINER, "Contenedor", "CT", "div", "card", transform.concat(C.CONTAINER, C.AUTO_LAYOUT), {
            style: { direction: "column", gap: 10 },
        }),
        component(T.MAP, "Google Maps", "MP", "div", "map", transform.concat(C.ACTIONABLE, C.DYNAMIC_DATA), {
            content: { source: "21.1225,-101.6834", zoom: 15, loading: "lazy" },
        }),
        component(T.VIDEO, "Video / YouTube", "VD", "div", "video", transform.concat(C.MEDIA, C.ACTIONABLE), {
            content: { sourceType: "youtube", source: "", controls: true, muted: true },
        }),
        component(T.RSVP, "RSVP", "RS", "div", "rsvp", transform.concat(C.DYNAMIC_DATA), {
            content: { title: "Confirma tu asistencia", showComment: true },
        }),
        component(T.COUNTDOWN, "Cuenta regresiva", "CDN", "div", "countdown", transform.concat(C.CONTAINER, C.DYNAMIC_DATA, C.COMPOSITE), {
            content: { targetDate: "", compositeVersion: 1 },
        }),
        component(T.ICON, "Icono", "IC", "span", "icon", transform.concat(C.ACTIONABLE), {
            content: { value: "✦" },
        }),
        component(T.SEPARATOR, "Separador", "—", "hr", "separator", transform, {
            style: { orientation: "horizontal", borderWidth: 1 },
        }),
    ];
}

function component(type, label, icon, element, inspector, capabilities, defaults) {
    return {
        type,
        version: "1.0.0",
        label,
        icon,
        element,
        inspector,
        renderer: type,
        category: "basic",
        capabilities,
        defaults,
    };
}
