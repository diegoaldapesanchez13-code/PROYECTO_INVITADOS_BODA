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
                    label: "Valor",
                    type: "text",
                    path: "interaction.action.value",
                    placeholder: "Destino de la interacción",
                    visibleWhen: ({ node }) => {
                        if (!interactionEnabled({ node })) {
                            return false;
                        }

                        return node.interaction
                            ?.action?.type
                            !== INTERACTION_TYPES.NONE;
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
                            getInteractionDefinition(
                                node.interaction
                                    ?.action?.type
                            )?.supportsNewTab
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
