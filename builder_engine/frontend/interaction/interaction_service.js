import { createInteraction, validateInteraction } from "./interaction_contract.js";

export class InteractionService {
    #registry;
    #contextFactory;

    constructor(registry, options = {}) {
        if (!registry?.get) throw new TypeError("InteractionService requiere InteractionRegistry.");
        this.#registry = registry;
        this.#contextFactory = options.contextFactory || (() => ({}));
    }

    normalize(value) {
        return createInteraction(value);
    }

    validate(value, context = {}) {
        const base = validateInteraction(value);
        if (!base.valid) return base;
        if (!base.value.enabled) return { valid: true, errors: [], value: base.value };
        const executor = this.#registry.get(base.value.action.type);
        const errors = executor.validate?.(
            base.value.action,
            this.#buildContext(context),
        ) || [];
        return { valid: errors.length === 0, errors, value: base.value };
    }

    async execute(value, context = {}) {
        const result = this.validate(value, context);
        if (!result.valid) throw new Error(result.errors.join("\n"));
        if (!result.value.enabled) {
            return { handled: false, reason: "disabled" };
        }
        const executor = this.#registry.get(result.value.action.type);
        return executor.execute(
            result.value.action,
            this.#buildContext(context),
        );
    }

    async trigger(node, trigger, context = {}) {
        const interactions = normalizeInteractionList(node?.interactions);
        const candidates = interactions.filter(
            (interaction) => interaction.enabled && interaction.trigger === String(trigger).toUpperCase(),
        );
        const results = [];
        for (const interaction of candidates) {
            results.push(await this.execute(interaction, { ...context, node }));
        }
        return results;
    }

    #buildContext(context) {
        return { ...this.#contextFactory(), ...context };
    }
}

function normalizeInteractionList(value) {
    if (Array.isArray(value)) return value.map(createInteraction);
    if (value && typeof value === "object") return [createInteraction(value)];
    return [];
}
