import assert from "node:assert/strict";
import { NODE_TYPES } from "../core/schema.js";
import { getComponentDefinition } from "../core/component_registry.js";
import { getInsertableComponent } from "../components/catalog.js";

assert.equal(getInsertableComponent("rsvp").type, NODE_TYPES.RSVP);
assert.equal(getComponentDefinition(NODE_TYPES.RSVP).inspectorPanel, "rsvp");
console.log("test_r3_rsvp_registry_contract: ok");
