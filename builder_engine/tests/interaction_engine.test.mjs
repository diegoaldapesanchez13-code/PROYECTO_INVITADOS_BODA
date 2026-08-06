import assert from "node:assert/strict";
import test from "node:test";
import {
    InteractionRegistry,
    InteractionService,
    createInteraction,
    registerInteractionModule,
    adaptR3Interaction,
} from "../frontend/interaction/index.js";
import { urlExecutor } from "../frontend/interaction/executors/url.js";
import { whatsappExecutor } from "../frontend/interaction/executors/whatsapp.js";
import { canvasExecutor } from "../frontend/interaction/executors/canvas.js";

test("InteractionRegistry registra ejecutores por tipo", () => {
    const registry = new InteractionRegistry();
    registry.register("URL", urlExecutor);
    assert.equal(registry.has("url"), true);
    assert.throws(() => registry.register("URL", urlExecutor), /ya está registrado/);
});

test("URL executor rechaza protocolos inseguros", () => {
    assert.deepEqual(urlExecutor.validate({ value: "javascript:alert(1)" }), ["La URL no es válida o segura."]);
    assert.deepEqual(urlExecutor.validate({ value: "https://example.com" }), []);
});

test("WhatsApp genera enlace wa.me", () => {
    const result = whatsappExecutor.execute({
        target: "+52 477 123 4567",
        payload: { message: "Hola" },
    });
    assert.match(result.url, /^https:\/\/wa\.me\/524771234567/);
    assert.match(result.url, /text=Hola/);
});

test("Canvas valida que el destino exista", () => {
    const context = { document: { canvases: [{ id: "principal" }] } };
    assert.deepEqual(canvasExecutor.validate({ target: "principal" }, context), []);
    assert.match(canvasExecutor.validate({ target: "otro" }, context)[0], /no existe/);
});

test("InteractionService ejecuta mediante puertos inyectados", async () => {
    const registry = new InteractionRegistry();
    registry.register("URL", urlExecutor);
    const calls = [];
    const service = new InteractionService(registry, {
        contextFactory: () => ({
            navigation: {
                openUrl(url, options) {
                    calls.push({ url, options });
                    return { ok: true };
                },
            },
        }),
    });
    const result = await service.execute(createInteraction({
        enabled: true,
        action: { type: "URL", value: "https://example.com", openInNewTab: true },
    }));
    assert.deepEqual(result, { ok: true });
    assert.equal(calls[0].options.newTab, true);
});

test("InteractionService dispara interacciones del nodo por trigger", async () => {
    const registry = new InteractionRegistry();
    registry.register("URL", urlExecutor);
    const service = new InteractionService(registry);
    const node = {
        interactions: [
            { enabled: true, trigger: "CLICK", action: { type: "URL", value: "/evento" } },
            { enabled: true, trigger: "SUBMIT", action: { type: "URL", value: "/confirmar" } },
        ],
    };
    const results = await service.trigger(node, "CLICK");
    assert.equal(results.length, 1);
    assert.equal(results[0].url, "/evento");
});

test("Adaptador R3 convierte SECTION en CANVAS", () => {
    const adapted = adaptR3Interaction({
        enabled: true,
        trigger: "CLICK",
        action: { type: "SECTION", target: "detalles" },
    });
    assert.equal(adapted.action.type, "CANVAS");
    assert.equal(adapted.action.target, "detalles");
});

test("InteractionModule registra ejecutores oficiales", () => {
    const modules = new Map();
    const app = {
        register(key, module) { modules.set(key, module); return module; },
        getDocument() { return { canvases: [] }; },
    };
    const module = registerInteractionModule(app);
    module.start({ app });
    assert.equal(module.registry.has("URL"), true);
    assert.equal(module.registry.has("WHATSAPP"), true);
    assert.equal(module.registry.has("GOOGLE_MAPS"), true);
    assert.equal(module.registry.has("CANVAS"), true);
});
