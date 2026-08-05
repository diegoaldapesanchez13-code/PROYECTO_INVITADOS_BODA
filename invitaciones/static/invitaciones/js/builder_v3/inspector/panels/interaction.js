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
                    key: "interactionValue",
                    label: "Valor / número",
                    type: "text",
                    path: "interaction.action.value",
                    placeholder: "Destino de la interacción",
                    visibleWhen: ({ node }) => {
                        if (!interactionEnabled({ node })) {
                            return false;
                        }

                        return interactionDefinition(node)
                            ?.valueControl
                            !== "hidden";
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
        node?.interaction?.action?.type
        || INTERACTION_TYPES.NONE
    );
}
