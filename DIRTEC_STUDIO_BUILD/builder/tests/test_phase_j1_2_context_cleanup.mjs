import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
    EVENT_BINDING_FIELDS,
    resolveDataBoundText,
} from "../data_bindings/index.js";
import {
    textPanel,
} from "../inspector/panels/text.js";

const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);

test("J1.2 generic Text exposes Manual/Event only", () => {
    const bindingGroup = textPanel().find(
        group => group.id === "data-binding"
    );
    const source = bindingGroup.fields.find(
        field => field.key === "bindingSource"
    );

    assert.deepEqual(
        source.options.map(item => item[0]),
        ["MANUAL", "EVENT"],
    );
    assert.equal(
        bindingGroup.fields.some(
            field =>
                field.key
                === "invitationBindingField"
        ),
        false,
    );
});

test("J1.2 event binding vocabulary is generic", () => {
    const keys = EVENT_BINDING_FIELDS.map(
        item => item[0]
    );

    assert.ok(keys.includes("primaryName"));
    assert.ok(keys.includes("secondaryName"));
    assert.ok(keys.includes("participantNames"));

    assert.equal(
        keys.includes("groomName"),
        false,
    );
    assert.equal(
        keys.includes("brideName"),
        false,
    );
});

test("J1.2 old invitation binding still resolves for compatibility", () => {
    assert.equal(
        resolveDataBoundText(
            {
                source: "INVITATION_GROUP",
                field: "groupName",
            },
            {
                invitationContext: {
                    groupName: "Familia Pérez",
                },
                fallback: "Invitación",
            }
        ),
        "Familia Pérez",
    );
});

test("J1.2 RSVP editable preview prefers real runtime guests", () => {
    const renderer = fs.readFileSync(
        path.join(
            root,
            "renderer/renderer.js",
        ),
        "utf8",
    );

    assert.match(
        renderer,
        /Array\.isArray\(invitationContext\.guests\)/,
    );
    assert.match(
        renderer,
        /runtimePreview/,
    );
});

test("J1.2 public RSVP GET bypasses browser cache", () => {
    const publicRuntime = fs.readFileSync(
        path.join(
            root,
            "public/public.js",
        ),
        "utf8",
    );

    assert.match(
        publicRuntime,
        /cache:\s*"no-store"/,
    );
});
