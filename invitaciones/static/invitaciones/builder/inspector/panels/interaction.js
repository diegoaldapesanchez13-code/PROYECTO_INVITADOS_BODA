import {
    field,
    group,
} from "../controls.js";

import {
    INTERACTION_TRIGGERS,
    INTERACTION_TYPES,
    getInteractionDefinition,
    interactionTypeOptions,
} from "../../interaction/index.js";

export function interactionPanel() {
    return [
        group({
            id: "interaction",
            title: "Interacción",
            description:
                "Configura el comportamiento al tocar esta capa.",
            fields: [
                field({
                    key: "interactionEnabled",
                    label: "Habilitar interacción",
                    type: "checkbox",
                    path: "interaction.enabled",
                }),
                field({
                    key: "interactionTrigger",
                    label: "Evento",
                    type: "select",
                    path: "interaction.trigger",
                    options: [
                        [
                            INTERACTION_TRIGGERS.CLICK,
                            "Click / toque",
                        ],
                    ],
                    visibleWhen: interactionEnabled,
                }),
                field({
                    key: "interactionType",
                    label: "Tipo",
                    type: "select",
                    path: "interaction.action.type",
                    options: interactionTypeOptions(),
                    visibleWhen: interactionEnabled,
                }),
                field({
                    key: "interactionCanvas",
                    label: "Lienzo de destino",
                    type: "select",
                    path: "interaction.action.value",
                    options: canvasOptions,
                    visibleWhen: ({ node }) =>
                        interactionEnabled({ node })
                        && interactionType(node)
                            === INTERACTION_TYPES.CANVAS,
                    help:
                        "Se guarda el ID estable del lienzo; renombrarlo o reordenarlo no rompe la navegación.",
                }),
                field({
                    key: "interactionValue",
                    label: "Valor / número",
                    type: "text",
                    path: "interaction.action.value",
                    placeholder: "Destino de la interacción",
                    visibleWhen: ({ node }) => {
                        if (!interactionEnabled({ node })) {
                            return false;
                        }

                        const definition =
                            interactionDefinition(node);

                        return definition
                            ?.valueControl
                            !== "hidden"
                            && definition
                                ?.valueControl
                                !== "canvas";
                    },
                }),
                field({
                    key: "interactionTarget",
                    label: "Mensaje opcional",
                    type: "textarea",
                    path: "interaction.action.target",
                    placeholder: "Hola, confirmo mi asistencia.",
                    visibleWhen: ({ node }) => {
                        if (!interactionEnabled({ node })) {
                            return false;
                        }

                        return interactionDefinition(node)
                            ?.targetControl
                            !== "hidden";
                    },
                }),
                field({
                    key: "interactionNewTab",
                    label: "Abrir en nueva pestaña",
                    type: "checkbox",
                    path: "interaction.action.openInNewTab",
                    visibleWhen: ({ node }) => {
                        if (!interactionEnabled({ node })) {
                            return false;
                        }

                        return Boolean(
                            interactionDefinition(node)
                                ?.supportsNewTab
                        );
                    },
                }),
            ],
        }),
    ];
}

function interactionEnabled({ node }) {
    return Boolean(
        node?.interaction?.enabled
    );
}

function interactionDefinition(node) {
    return getInteractionDefinition(
        interactionType(node)
    );
}

function interactionType(node) {
    return node?.interaction?.action?.type
        || INTERACTION_TYPES.NONE;
}

function canvasOptions({ state }) {
    const canvass = [
        ...(state?.document?.canvases || []),
    ].sort(
        (a, b) =>
            Number(a.order || 0)
            - Number(b.order || 0)
    );

    return [
        ["", "Selecciona un lienzo"],
        ...canvases.map(
            (canvas, index) => [
                canvas.id,
                canvas.name
                    || `Lienzo ${index + 1}`,
            ]
        ),
    ];
}
