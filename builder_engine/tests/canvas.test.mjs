import assert from "node:assert/strict";
import test from "node:test";
import { BuilderApp } from "../frontend/app/index.js";
import { registerCanvasModule } from "../frontend/canvas/index.js";

test("CanvasModule se registra e inicia con un lienzo", async () => {
    const app = new BuilderApp();
    const module = registerCanvasModule(app);
    await app.start();
    assert.equal(app.registry.get("canvas"), module);
    assert.equal(module.service.list().length, 1);
    assert.equal(module.service.selectedId, module.service.list()[0].id);
    await app.destroy();
});

test("CanvasService crea, duplica, reordena y elimina lienzos", async () => {
    const app = new BuilderApp();
    const module = registerCanvasModule(app);
    await app.start();
    const service = module.service;
    const first = service.list()[0];
    const second = service.create({ name: "Recepción", height: 900 });
    const copy = service.duplicate(second.id);
    assert.deepEqual(service.list().map((canvas) => canvas.name), [first.name, "Recepción", "Recepción copia"]);
    service.move(copy.id, 0);
    assert.equal(service.list()[0].id, copy.id);
    assert.equal(service.remove(second.id), true);
    assert.equal(service.list().length, 2);
    assert.equal(app.isDirty, true);
    await app.destroy();
});

test("CanvasService protege el último lienzo y lienzos bloqueados", async () => {
    const app = new BuilderApp();
    const module = registerCanvasModule(app);
    await app.start();
    const service = module.service;
    const first = service.list()[0];
    assert.equal(service.remove(first.id), false);
    service.update(first.id, { locked: true });
    assert.equal(service.remove(first.id, { allowEmpty: true }), false);
    await app.destroy();
});
