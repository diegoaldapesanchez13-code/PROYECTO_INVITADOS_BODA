import assert from "node:assert/strict";

import {
    COMPONENT_CAPABILITIES,
    NODE_TYPES,
    componentSupports,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
    getInteractionDefinition,
    interactionTypeOptions,
    listInteractionDefinitions,
    requireInteractionDefinition,
} from "../interaction/index.js";

import {
    interactionPanel,
} from "../inspector/panels/interaction.js";

const definitions = listInteractionDefinitions();
const types = new Set(
    definitions.map((item) => item.type)
);

for (const type of Object.values(INTERACTION_TYPES)) {
    assert.equal(
        types.has(type),
        true,
        `Falta registrar ${type}`
    );

    assert.equal(
        requireInteractionDefinition(type).type,
        type
    );
}

assert.equal(
    getInteractionDefinition("UNKNOWN"),
    null
);
assert.throws(
    () => requireInteractionDefinition("UNKNOWN"),
    /Interacción no registrada/
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
        NODE_TYPES.TEXT,
        COMPONENT_CAPABILITIES.ACTIONABLE
    ),
    true
);
assert.equal(
    componentSupports(
        NODE_TYPES.BUTTON,
        COMPONENT_CAPABILITIES.ACTIONABLE
    ),
    true
);
assert.equal(
    componentSupports(
        NODE_TYPES.SECTION,
        COMPONENT_CAPABILITIES.ACTIONABLE
    ),
    false
);

const options = interactionTypeOptions();
assert.equal(
    options.some(
        ([value]) => value === INTERACTION_TYPES.GOOGLE_MAPS
    ),
    true
);

const panels = interactionPanel();
assert.equal(panels.length, 1);
assert.equal(panels[0].id, "interaction");

const enabledField = panels[0].fields.find(
    (item) => item.path === "interaction.enabled"
);
const typeField = panels[0].fields.find(
    (item) => item.path === "interaction.action.type"
);

assert.ok(enabledField);
assert.ok(typeField);
assert.equal(
    typeof typeField.visibleWhen,
    "function"
);

const copy = getInteractionDefinition(
    INTERACTION_TYPES.URL
);
copy.label = "Mutado";

assert.notEqual(
    getInteractionDefinition(
        INTERACTION_TYPES.URL
    ).label,
    "Mutado",
    "El registro no expone referencias mutables"
);

console.log(
    `OK interaction registry: ${definitions.length} tipos`
);
