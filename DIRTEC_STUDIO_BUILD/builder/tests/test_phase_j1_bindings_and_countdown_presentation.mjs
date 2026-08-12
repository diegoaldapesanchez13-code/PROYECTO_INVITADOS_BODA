import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
    DATA_BINDING_SOURCES,
    resolveDataBoundText,
} from "../data_bindings/index.js";
import { BuilderState } from "../core/state.js";
import {
    createEmptyDocument,
    NODE_TYPES,
} from "../core/schema.js";
import {
    insertComponent,
} from "../components/factory.js";
import {
    countdownPanel,
} from "../inspector/panels/countdown.js";
import {
    textPanel,
} from "../inspector/panels/text.js";

const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);

test("J1 resolves EVENT text and keeps fallback", () => {
    assert.equal(
        resolveDataBoundText(
            {
                source: DATA_BINDING_SOURCES.EVENT,
                field: "coupleNames",
            },
            {
                eventContext: {
                    coupleNames: "Diego & Fernanda",
                },
                fallback: "Pareja",
            }
        ),
        "Diego & Fernanda",
    );

    assert.equal(
        resolveDataBoundText(
            {
                source: DATA_BINDING_SOURCES.EVENT,
                field: "missing",
            },
            {
                eventContext: {},
                fallback: "Texto manual",
            }
        ),
        "Texto manual",
    );
});

test("J1 resolves invitation group data", () => {
    assert.equal(
        resolveDataBoundText(
            {
                source:
                    DATA_BINDING_SOURCES.INVITATION_GROUP,
                field: "groupName",
            },
            {
                invitationContext: {
                    groupName: "Familia Pérez",
                },
            }
        ),
        "Familia Pérez",
    );
});

test("J1 text Inspector exposes dynamic binding without touching countdown text", () => {
    const panels = textPanel();
    const binding = panels.find(
        panel => panel.id === "data-binding"
    );
    assert.ok(binding);

    assert.equal(
        binding.visibleWhen({
            node: {
                content: {
                    binding: {
                        source: "COUNTDOWN",
                    },
                },
            },
        }),
        false,
    );

    const source = binding.fields.find(
        field => field.key === "bindingSource"
    );
    assert.ok(source);
    assert.deepEqual(
        source.options.map(item => item[0]),
        ["MANUAL", "EVENT"],
    );
});

test("J1 countdown defaults to CARDS with labels", () => {
    const state = new BuilderState(
        createEmptyDocument()
    );
    const canvas = state.createNode(
        NODE_TYPES.CANVAS,
        {
            name: "Lienzo",
            height: 900,
        }
    );
    const countdown = insertComponent({
        state,
        type: NODE_TYPES.COUNTDOWN,
        selectedNodeId: canvas.id,
    });

    assert.equal(
        countdown.content.presentation,
        "CARDS",
    );
    assert.equal(
        countdown.content.showLabels,
        true,
    );

    const units = state.getChildren(
        countdown.id
    );
    assert.equal(units.length, 4);
    assert.ok(
        units.every(
            node => node.type === NODE_TYPES.CARD
        )
    );
});

test("J1 countdown Inspector provides Cards/Plain and labels toggle", () => {
    const group = countdownPanel().find(
        panel =>
            panel.id
            === "countdown-presentation"
    );

    assert.ok(group);
    const presentation = group.fields.find(
        field =>
            field.key
            === "countdownPresentation"
    );
    const labels = group.fields.find(
        field =>
            field.key
            === "countdownShowLabels"
    );

    assert.deepEqual(
        presentation.options,
        [
            ["CARDS", "Cards"],
            ["PLAIN", "Sin cards"],
        ],
    );
    assert.equal(
        labels.path,
        "content.showLabels",
    );
});

test("J1 renderer CSS hides card chrome without deleting composite structure", () => {
    const css = fs.readFileSync(
        path.join(
            root,
            "renderer/renderer.css",
        ),
        "utf8",
    );

    assert.match(
        css,
        /data-r3-countdown-presentation="PLAIN"/,
    );
    assert.match(
        css,
        /background:\s*transparent\s*!important/,
    );
    assert.match(
        css,
        /data-r3-countdown-show-labels="0"/,
    );
});
