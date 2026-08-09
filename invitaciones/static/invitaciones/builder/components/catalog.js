import {
    NODE_TYPES,
} from "../core/index.js?v=f4-native-v4-freeze";

const COMPONENT_CATALOG = Object.freeze([
    item("text", NODE_TYPES.TEXT, "Texto", "Agrega una capa de texto editable.", "T", "Básicos"),
    item("button", NODE_TYPES.BUTTON, "Botón", "Agrega un botón editable con interacción.", "BT", "Básicos"),
    item("card", NODE_TYPES.CARD, "Card", "Contenedor visual con fondo, borde y capas hijas.", "CD", "Estructura"),
    item("container", NODE_TYPES.CONTAINER, "Contenedor", "Agrupa capas sin imponer apariencia visual.", "CT", "Estructura"),
    item("map", NODE_TYPES.MAP, "Google Maps", "Agrega un mapa interactivo, redimensionable y editable.", "MP", "Contenido"),
    item("video", NODE_TYPES.VIDEO, "Video / YouTube", "Agrega video directo o un reproductor de YouTube.", "VD", "Contenido"),
    item("rsvp", NODE_TYPES.RSVP, "RSVP", "Agrega la confirmación conectada al UUID de la invitación.", "RS", "Contenido"),
    item("countdown", NODE_TYPES.COUNTDOWN, "Cuenta regresiva", "Agrega días, horas, minutos y segundos personalizables.", "CDN", "Contenido"),
    item("separator", NODE_TYPES.SEPARATOR, "Separador", "Agrega una línea horizontal o vertical editable.", "—", "Estructura"),
    item("icon", NODE_TYPES.ICON, "Icono", "Agrega un símbolo o carácter editable como capa.", "IC", "Contenido"),
]);

export function listInsertableComponents() {
    return COMPONENT_CATALOG.map(clone);
}

export function getInsertableComponent(idOrType) {
    const value = String(idOrType || "");
    const found = COMPONENT_CATALOG.find(
        (entry) => entry.id === value || entry.type === value
    );

    return found ? clone(found) : null;
}

function item(id, type, label, description, icon, category) {
    return Object.freeze({
        id,
        type,
        label,
        description,
        icon,
        category,
    });
}

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}
