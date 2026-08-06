import assert from "node:assert/strict";
import test from "node:test";
import {
    COMPONENT_LIBRARY_ITEMS,
    groupLibraryItems,
    insertionPosition,
    componentInsertOptions,
} from "../frontend/workspace/component_library.js";

test("incluye componentes esenciales", () => {
    const ids = COMPONENT_LIBRARY_ITEMS.map((item) => item.id);
    for (const id of ["heading", "paragraph", "button", "image", "video", "card", "container", "countdown"]) {
        assert.equal(ids.includes(id), true);
    }
});

test("agrupa componentes por categoría", () => {
    const groups = groupLibraryItems();
    assert.equal(groups.some((group) => group.category === "Texto"), true);
    assert.equal(groups.some((group) => group.category === "Media"), true);
});

test("calcula posiciones escalonadas", () => {
    const first = insertionPosition([]);
    const second = insertionPosition([{ style: { zIndex: 3 }, children: [] }]);

    assert.equal(first.y, 24);
    assert.equal(second.y, 24);
    assert.notEqual(first.x, second.x);
    assert.equal(second.zIndex, 4);
});

test("prepara inserción de texto", () => {
    const item = COMPONENT_LIBRARY_ITEMS.find((entry) => entry.id === "heading");
    const prepared = componentInsertOptions(item, { id: "canvas-1", nodes: [] });

    assert.equal(prepared.typeOrBlueprint, "TEXT");
    assert.equal(prepared.options.overrides.content.text, "Título principal");
    assert.equal(prepared.options.overrides.style.y, 24);
});

test("prepara Countdown como blueprint", () => {
    const item = COMPONENT_LIBRARY_ITEMS.find((entry) => entry.id === "countdown");
    const prepared = componentInsertOptions(item, { id: "canvas-1", nodes: [] });

    assert.equal(prepared.typeOrBlueprint, "countdown");
    assert.equal(prepared.options.blueprint, true);
    assert.equal(prepared.options.context.canvasId, "canvas-1");
});

test("respeta posición de drop", () => {
    const item = COMPONENT_LIBRARY_ITEMS.find((entry) => entry.id === "button");
    const prepared = componentInsertOptions(
        item,
        { id: "canvas-1", nodes: [] },
        { position: { x: 32, y: 61 } },
    );

    assert.equal(prepared.options.overrides.style.x, 32);
    assert.equal(prepared.options.overrides.style.y, 61);
});
