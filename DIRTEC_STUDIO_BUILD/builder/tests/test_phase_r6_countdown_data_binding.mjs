import assert from "node:assert/strict";
import test from "node:test";

import { UniversalRenderer } from "../renderer/renderer.js";
import { BuilderState } from "../core/state.js";
import { createEmptyDocument, NODE_TYPES } from "../core/schema.js";
import { insertComponent } from "../components/factory.js";
import { countdownPanel } from "../inspector/panels/countdown.js";

const eventContext = {
    eventDate: "2030-01-01T10:00:00Z",
    ceremonyDate: "2030-01-01T12:00:00Z",
    receptionDate: "2030-01-01T18:00:00Z",
};

function renderer() {
    const value = Object.create(UniversalRenderer.prototype);
    value.options = { eventContext };
    return value;
}

test("R6 new countdown defaults to reception binding", () => {
    const state = new BuilderState(createEmptyDocument());
    const canvas = state.createNode(
        NODE_TYPES.CANVAS,
        { name: "Lienzo", height: 900 },
    );
    const countdown = insertComponent({
        state,
        type: NODE_TYPES.COUNTDOWN,
        selectedNodeId: canvas.id,
    });

    assert.equal(
        countdown.content.targetSource,
        "RECEPTION",
    );
});

test("R6 resolves EVENT CEREMONY RECEPTION and CUSTOM", () => {
    const r = renderer();

    assert.equal(
        r.resolveCountdownTarget({
            content: { targetSource: "EVENT" },
        }),
        Date.parse(eventContext.eventDate),
    );
    assert.equal(
        r.resolveCountdownTarget({
            content: { targetSource: "CEREMONY" },
        }),
        Date.parse(eventContext.ceremonyDate),
    );
    assert.equal(
        r.resolveCountdownTarget({
            content: { targetSource: "RECEPTION" },
        }),
        Date.parse(eventContext.receptionDate),
    );
    assert.equal(
        r.resolveCountdownTarget({
            content: {
                targetSource: "CUSTOM",
                targetDate: "2031-05-06T19:30:00Z",
            },
        }),
        Date.parse("2031-05-06T19:30:00Z"),
    );
});

test("R6 preserves legacy manual countdowns", () => {
    const r = renderer();
    const target = "2032-02-03T14:15:00Z";

    assert.equal(
        r.resolveCountdownTarget({
            content: { targetDate: target },
        }),
        Date.parse(target),
    );
});

test("R6 old empty countdown falls forward to event reception", () => {
    const r = renderer();

    assert.equal(
        r.resolveCountdownTarget({
            content: {},
        }),
        Date.parse(eventContext.receptionDate),
    );
});

test("R6 countdown inspector exposes source and custom date", async () => {
    const groups = countdownPanel();
    const fields = groups[0].fields;
    const source = fields.find(
        field => field.key === "targetSource"
    );
    const custom = fields.find(
        field => field.key === "targetDate"
    );

    assert.ok(source);
    assert.deepEqual(
        source.options.map(option => option[0]),
        ["RECEPTION", "CEREMONY", "EVENT", "CUSTOM"],
    );
    assert.equal(
        custom.visibleWhen({
            node: {
                content: {
                    targetSource: "CUSTOM",
                },
            },
        }),
        true,
    );
    assert.equal(
        custom.visibleWhen({
            node: {
                content: {
                    targetSource: "RECEPTION",
                },
            },
        }),
        false,
    );

    let refreshed = 0;
    source.onChange({
        inspector: {
            refresh() {
                refreshed += 1;
            },
        },
    });
    await Promise.resolve();
    assert.equal(refreshed, 1);
});
