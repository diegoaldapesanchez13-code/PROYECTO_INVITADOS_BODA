import assert from "node:assert/strict";

import {
    COMPONENT_CAPABILITIES,
    NODE_TYPES,
    componentElementName,
    componentIcon,
    componentLabel,
    componentSupports,
    getComponentDefinition,
    isContainerComponent,
    listComponentDefinitions,
    requireComponentDefinition,
} from "../core/index.js";

const definitions = listComponentDefinitions();
const registeredTypes = new Set(
    definitions.map((item) => item.type)
);

for (const type of Object.values(NODE_TYPES)) {
    assert.equal(
        registeredTypes.has(type),
        true,
        `Falta registrar ${type}`
    );

    const definition = requireComponentDefinition(type);
    assert.equal(definition.type, type);
    assert.equal(typeof componentLabel(type), "string");
    assert.equal(typeof componentIcon(type), "string");
    assert.equal(typeof componentElementName(type), "string");
}

assert.equal(
    isContainerComponent(NODE_TYPES.SECTION),
    true
);
assert.equal(
    isContainerComponent(NODE_TYPES.CARD),
    true
);
assert.equal(
    isContainerComponent(NODE_TYPES.TEXT),
    false
);
assert.equal(
    componentSupports(
        NODE_TYPES.IMAGE,
        COMPONENT_CAPABILITIES.ACTIONABLE
    ),
    true
);
assert.equal(
    componentSupports(
        NODE_TYPES.COUNTDOWN,
        COMPONENT_CAPABILITIES.DYNAMIC_DATA
    ),
    true
);
assert.equal(
    getComponentDefinition("UNKNOWN"),
    null
);
assert.throws(
    () => requireComponentDefinition("UNKNOWN"),
    /Componente no registrado/
);

const textDefinition = getComponentDefinition(
    NODE_TYPES.TEXT
);
textDefinition.capabilities.push("MUTATION_TEST");

assert.equal(
    getComponentDefinition(NODE_TYPES.TEXT)
        .capabilities
        .includes("MUTATION_TEST"),
    false,
    "El registro no debe exponer referencias mutables"
);

console.log(
    `OK component registry: ${definitions.length} tipos registrados`
);
