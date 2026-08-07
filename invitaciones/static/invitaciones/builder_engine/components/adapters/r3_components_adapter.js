/**
 * Adapta definiciones del Component Registry de Builder R3 al contrato del Engine.
 */
export function adaptR3ComponentDefinition(definition = {}) {
    return {
        type: String(definition.type || "").toUpperCase(),
        version: "1.0.0-r3",
        label: definition.label,
        icon: definition.icon,
        element: definition.element,
        inspector: definition.inspectorPanel,
        renderer: definition.customRenderer || definition.type,
        legacy: Boolean(definition.legacy),
        capabilities: Array.isArray(definition.capabilities)
            ? [...definition.capabilities]
            : [],
        defaults: definition.defaults || {},
    };
}

export function adaptR3ComponentDefinitions(definitions = []) {
    return definitions.map(adaptR3ComponentDefinition);
}
