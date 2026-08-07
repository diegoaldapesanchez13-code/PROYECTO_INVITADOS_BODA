import assert from "node:assert/strict";
import test from "node:test";
import { BuilderApp } from "../frontend/app/index.js";
import { createDocument } from "../frontend/document/index.js";
import { registerHistoryModule } from "../frontend/history/index.js";

function appWithTitle(title = "Inicial") {
    return new BuilderApp({
        document: createDocument({ metadata: { name: title } }),
    });
}

test("HistoryModule registra undo y redo", async () => {
    const app = appWithTitle();
    const history = registerHistoryModule(app);
    await app.start();

    app.updateDocument((document) => {
        document.metadata.name = "Cambio 1";
    }, { label: "Renombrar" });

    assert.equal(history.service.canUndo, true);
    assert.equal(history.service.undo(), true);
    assert.equal(app.getDocument().metadata.name, "Inicial");
    assert.equal(history.service.redo(), true);
    assert.equal(app.getDocument().metadata.name, "Cambio 1");

    await app.destroy();
});

test("HistoryModule agrupa una transacción en un solo paso", async () => {
    const app = appWithTitle();
    const history = registerHistoryModule(app);
    await app.start();

    history.service.beginTransaction({ label: "Mover capa" });
    for (const x of [10, 20, 30, 40]) {
        app.updateDocument((document) => {
            document.globals.positionX = x;
        }, { label: "Movimiento" });
    }
    assert.equal(history.service.length, 1);
    assert.equal(history.service.commitTransaction(), true);
    assert.equal(history.service.length, 2);

    history.service.undo();
    assert.equal(app.getDocument().globals.positionX, undefined);

    await app.destroy();
});

test("HistoryModule combina escritura consecutiva por mergeKey", async () => {
    const app = appWithTitle();
    const history = registerHistoryModule(app, { mergeWindowMs: 5000 });
    await app.start();

    for (const name of ["H", "Ho", "Hol", "Hola"]) {
        app.updateDocument((document) => {
            document.metadata.name = name;
        }, { label: "Escribir título", mergeKey: "metadata.name" });
    }

    assert.equal(history.service.length, 2);
    history.service.undo();
    assert.equal(app.getDocument().metadata.name, "Inicial");

    await app.destroy();
});

test("HistoryModule elimina el futuro después de editar tras undo", async () => {
    const app = appWithTitle();
    const history = registerHistoryModule(app);
    await app.start();

    app.updateDocument((document) => { document.metadata.name = "Uno"; });
    app.updateDocument((document) => { document.metadata.name = "Dos"; });
    history.service.undo();
    assert.equal(history.service.canRedo, true);

    app.updateDocument((document) => { document.metadata.name = "Alternativo"; });
    assert.equal(history.service.canRedo, false);
    assert.equal(app.getDocument().metadata.name, "Alternativo");

    await app.destroy();
});

test("HistoryModule permite viajar a una entrada concreta", async () => {
    const app = appWithTitle();
    const history = registerHistoryModule(app);
    await app.start();

    app.updateDocument((document) => { document.metadata.name = "Uno"; }, { label: "Uno" });
    app.updateDocument((document) => { document.metadata.name = "Dos"; }, { label: "Dos" });

    history.service.goTo(0);
    assert.equal(app.getDocument().metadata.name, "Inicial");
    assert.equal(history.service.timeline()[0].current, true);

    await app.destroy();
});
