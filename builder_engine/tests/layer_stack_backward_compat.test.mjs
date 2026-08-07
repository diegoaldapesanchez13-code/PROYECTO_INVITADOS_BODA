import assert from "node:assert/strict";
import test from "node:test";

import { LayerStackService } from "../frontend/layers/layer_stack_service.js";

function fixture() {
    return [
        { id: "a", style: {}, children: [] },
        { id: "b", style: {}, children: [] },
        { id: "c", style: {}, children: [] },
    ];
}

test("resultado conserva API histórica de arreglo", () => {
    const service = new LayerStackService();
    const result = service.bringToFront(
        service.normalize(fixture()),
        "a",
    );

    assert.equal(Array.isArray(result), true);
    assert.deepEqual(result.map((node) => node.id), ["b", "c", "a"]);
});

test("resultado expone API nueva nodes y transaction", () => {
    const service = new LayerStackService();
    const result = service.sendToBack(
        service.normalize(fixture()),
        "c",
    );

    assert.equal(result.nodes, result);
    assert.deepEqual(result.nodes.map((node) => node.id), ["c", "a", "b"]);
    assert.equal(result.transaction.operation, "REORDER");
});

test("propiedades auxiliares no contaminan serialización", () => {
    const service = new LayerStackService();
    const result = service.bringForward(
        service.normalize(fixture()),
        "a",
    );

    const parsed = JSON.parse(JSON.stringify(result));
    assert.deepEqual(parsed.map((node) => node.id), ["b", "a", "c"]);
    assert.equal(Object.hasOwn(parsed, "transaction"), false);
});
