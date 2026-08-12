import {
    field,
    group,
} from "../controls.js";

const TARGET_SOURCES = Object.freeze([
    ["RECEPTION", "Recepción / fiesta"],
    ["CEREMONY", "Ceremonia"],
    ["EVENT", "Inicio general del evento"],
    ["CUSTOM", "Fecha personalizada"],
]);

export function countdownPanel() {
    return [
        group({
            id: "countdown-data",
            title: "Datos de la cuenta regresiva",
            description:
                "La fecha puede venir directamente del evento en Django o definirse manualmente.",
            fields: [
                field({
                    key: "targetSource",
                    label: "Origen de fecha",
                    type: "select",
                    path: "content.targetSource",
                    options: TARGET_SOURCES,
                    help:
                        "Recepción usa la fecha de fiesta; Ceremonia usa la fecha de misa; Inicio general toma la primera fecha del evento.",
                    onChange: ({
                        inspector,
                    }) => {
                        // The Inspector intentionally does not rebuild for
                        // ordinary live controls. This source selector is the
                        // exception because it changes field visibility.
                        queueMicrotask(
                            () => inspector.refresh()
                        );
                        return null;
                    },
                }),
                field({
                    key: "targetDate",
                    label: "Fecha personalizada",
                    type: "datetime-local",
                    path: "content.targetDate",
                    visibleWhen: ({ node }) =>
                        effectiveSource(node)
                        === "CUSTOM",
                    help:
                        "Solo se usa cuando el origen es Fecha personalizada.",
                }),
                numericValue(
                    "days",
                    "Vista previa · Días",
                    "content.values.0",
                    0,
                    9999,
                ),
                numericValue(
                    "hours",
                    "Vista previa · Horas",
                    "content.values.1",
                    0,
                    23,
                ),
                numericValue(
                    "minutes",
                    "Vista previa · Minutos",
                    "content.values.2",
                    0,
                    59,
                ),
                numericValue(
                    "seconds",
                    "Vista previa · Segundos",
                    "content.values.3",
                    0,
                    59,
                ),
            ],
        }),
        group({
            id: "countdown-presentation",
            title: "Presentación",
            description:
                "Las Cards siguen existiendo como contenedores para no perder Número/Etiqueta, pero pueden ocultarse visualmente.",
            fields: [
                field({
                    key: "countdownPresentation",
                    label: "Estilo",
                    type: "select",
                    path: "content.presentation",
                    options: [
                        ["CARDS", "Cards"],
                        ["PLAIN", "Sin cards"],
                    ],
                }),
                field({
                    key: "countdownShowLabels",
                    label: "Mostrar etiquetas",
                    type: "checkbox",
                    path: "content.showLabels",
                    help:
                        "Desactívalo si quieres mostrar únicamente los números.",
                }),
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

function effectiveSource(node) {
    const configured =
        String(
            node?.content?.targetSource
            || ""
        ).toUpperCase();

    if (configured) {
        return configured;
    }

    // Backwards compatibility: old countdowns with a manual targetDate keep
    // using that exact value after R.6.
    return node?.content?.targetDate
        ? "CUSTOM"
        : "RECEPTION";
}

function numericValue(
    key,
    label,
    path,
    min,
    max,
) {
    return field({
        key,
        label,
        type: "number",
        path,
        min,
        max,
        step: 1,
    });
}
