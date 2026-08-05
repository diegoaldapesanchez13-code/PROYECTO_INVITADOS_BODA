import {
    NODE_TYPES,
} from "../core/index.js";

const COMPONENT_CATALOG = Object.freeze([
    Object.freeze({
        id: "text",
        type: NODE_TYPES.TEXT,
        label: "Texto",
        description: "Agrega una capa de texto editable.",
        icon: "T",
        category: "Básicos",
    }),
    Object.freeze({
        id: "button",
        type: NODE_TYPES.BUTTON,
        label: "Botón",
        description: "Agrega un botón editable con interacción.",
        icon: "BT",
        category: "Básicos",
    }),
]);

export function listInsertableComponents() {
    return COMPONENT_CATALOG.map(clone);
}

export function getInsertableComponent(idOrType) {
    const value = String(idOrType || "");
    const item = COMPONENT_CATALOG.find(
        (entry) => entry.id === value || entry.type === value
    );

    return item ? clone(item) : null;
}

function clone(value) {
    return JSON.parse(JSON.stringify(value));
}
