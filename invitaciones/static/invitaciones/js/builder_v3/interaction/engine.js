import {
    INTERACTION_TRIGGERS,
    normalizeInteraction,
} from "./defaults.js";

import {
    requireInteractionDefinition,
} from "./registry.js";

import {
    createDefaultInteractionExecutors,
} from "./executors/index.js";

export class InteractionEngine {
    constructor(options = {}) {
        const {
            definitionResolver =
                requireInteractionDefinition,
            executors =
                createDefaultInteractionExecutors(),
        } = options;

        if (
            typeof definitionResolver
            !== "function"
        ) {
            throw new TypeError(
                "definitionResolver debe ser una función."
            );
        }

        this.definitionResolver =
            definitionResolver;
        this.executors = normalizeExecutors(
            executors
        );
    }

    registerExecutor(type, executor) {
        if (typeof executor !== "function") {
            throw new TypeError(
                "executor debe ser una función."
            );
        }

        this.executors.set(
            String(type),
            executor
        );

        return this;
    }

    hasExecutor(type) {
        return this.executors.has(
            String(type)
        );
    }

    execute(node, options = {}) {
        const interaction =
            normalizeInteraction(
                node?.interaction
            );

        if (!interaction.enabled) {
            return skipped(
                "interaction-disabled"
            );
        }

        const trigger =
            options.trigger
            || INTERACTION_TRIGGERS.CLICK;

        if (interaction.trigger !== trigger) {
            return skipped(
                "trigger-mismatch",
                {
                    expected:
                        interaction.trigger,
                    received: trigger,
                }
            );
        }

        const definition =
            this.definitionResolver(
                interaction.action.type
            );

        const executor =
            this.executors.get(
                definition.type
            );

        if (!executor) {
            throw new Error(
                `No existe executor para ${definition.type}`
            );
        }

        const context = Object.freeze({
            node: clone(node || {}),
            interaction:
                clone(interaction),
            action:
                clone(interaction.action),
            definition:
                clone(definition),
            trigger,
            event:
                options.event || null,
            document:
                options.document
                    ? clone(options.document)
                    : null,
            metadata:
                clone(options.metadata || {}),
        });

        const result = executor(context);

        if (
            !result
            || typeof result !== "object"
        ) {
            throw new Error(
                `Executor inválido para ${definition.type}`
            );
        }

        return clone({
            ...result,
            interactionType:
                definition.type,
            trigger,
            nodeId:
                node?.id || null,
        });
    }
}

function normalizeExecutors(value) {
    if (value instanceof Map) {
        return new Map(value);
    }

    if (
        value
        && typeof value === "object"
        && !Array.isArray(value)
    ) {
        return new Map(
            Object.entries(value)
        );
    }

    throw new TypeError(
        "executors debe ser Map u objeto."
    );
}

function skipped(reason, details = {}) {
    return {
        handled: false,
        status: "skipped",
        reason,
        interactionType: null,
        trigger: null,
        nodeId: null,
        ...clone(details),
    };
}

function clone(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}
