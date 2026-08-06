import assert from "node:assert/strict";
import test from "node:test";
import {
    ComponentRegistry,
    ComponentFactory,
    COMPONENT_CAPABILITIES,
    builtinComponentDefinitions,
    registerComponentsModule,
    adaptR3ComponentDefinition,
} from "../frontend/components/index.js";

test("ComponentRegistry registra y consulta capacidades", () => {
    const registry = new ComponentRegistry();
    registry.registerMany(builtinComponentDefinitions());
    assert.equal(registry.has("text"), true);
    assert.equal(registry.supports("CARD", COMPONENT_CAPABILITIES.CONTAINER), true);
    assert.equal(registry.supports("TEXT", COMPONENT_CAPABILITIES.MEDIA), false);
});

test("ComponentRegistry evita tipos duplicados", () => {
    const registry = new ComponentRegistry();
    registry.register({ type: "TEXT" });
    assert.throws(() => registry.register({ type: "text" }), /ya está registrado/);
});

test("ComponentFactory aplica defaults y overrides sin mutar definición", () => {
    const registry = new ComponentRegistry();
    registry.registerMany(builtinComponentDefinitions());
    const factory = new ComponentFactory(registry, { idFactory: (type) => `${type}-1` });
    const node = factory.create("TEXT", { content: { text: "Hola" } });
    assert.equal(node.id, "TEXT-1");
    assert.equal(node.content.text, "Hola");
    assert.equal(node.content.tag, "p");
    assert.equal(registry.get("TEXT").defaults.content.text, "Escribe aquí");
});

test("Countdown Blueprint genera Cards y textos independientes", async () => {
    const document = { canvases: [{ id: "canvas-1", nodes: [] }] };
    const listeners = new Set();
    const modules = new Map();
    const app = {
        register(key, module) { modules.set(key, module); return module; },
        updateDocument(mutator) { mutator(document); for (const l of listeners) l({ type: "document:changed", payload: {} }); },
        getDocument() { return structuredClone(document); },
        subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    };
    const module = registerComponentsModule(app);
    module.start({ app });
    const countdown = module.service.createBlueprint("countdown");
    assert.equal(countdown.type, "COUNTDOWN");
    assert.equal(countdown.children.length, 4);
    assert.equal(countdown.children[0].type, "CARD");
    assert.equal(countdown.children[0].children.length, 2);
    assert.equal(countdown.children[0].children[0].content.binding.role, "value");
});

test("ComponentsService inserta un nodo en el Documento", () => {
    const document = { canvases: [{ id: "canvas-1", nodes: [] }] };
    const app = {
        register() {},
        updateDocument(mutator) { mutator(document); },
    };
    const module = registerComponentsModule(app);
    module.start({ app });
    const node = module.service.insert("canvas-1", "BUTTON", { overrides: { content: { label: "Confirmar" } } });
    assert.equal(document.canvases[0].nodes.length, 1);
    assert.equal(node.content.label, "Confirmar");
});

test("Adaptador R3 conserva inspector y capacidades", () => {
    const adapted = adaptR3ComponentDefinition({
        type: "MAP",
        label: "Google Maps",
        inspectorPanel: "map",
        capabilities: ["TRANSFORM"],
    });
    assert.equal(adapted.type, "MAP");
    assert.equal(adapted.inspector, "map");
    assert.deepEqual(adapted.capabilities, ["TRANSFORM"]);
});
