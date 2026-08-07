import {
    field,
    group,
} from "../controls.js";

export function countdownPanel() {
    return [
        group({
            id: "countdown-data",
            title: "Datos de la cuenta regresiva",
            description:
                "Cada unidad, número y etiqueta es una capa independiente. Selecciónala en Capas para moverla y diseñarla.",
            fields: [
                field({
                    key: "targetDate",
                    label: "Fecha objetivo",
                    type: "datetime-local",
                    path: "content.targetDate",
                }),
                numericValue("days", "Vista previa · Días", "content.values.0", 0, 9999),
                numericValue("hours", "Vista previa · Horas", "content.values.1", 0, 23),
                numericValue("minutes", "Vista previa · Minutos", "content.values.2", 0, 59),
                numericValue("seconds", "Vista previa · Segundos", "content.values.3", 0, 59),
            ],
        }),
        group({
            id: "countdown-help",
            title: "Edición por capas",
            description:
                "Expande Cuenta regresiva en Capas. Días, Horas, Minutos y Segundos son Cards; Número y Etiqueta son textos independientes.",
            fields: [],
            open: true,
        }),
    ];
}

function numericValue(key, label, path, min, max) {
    return field({ key, label, type: "number", path, min, max, step: 1 });
}
