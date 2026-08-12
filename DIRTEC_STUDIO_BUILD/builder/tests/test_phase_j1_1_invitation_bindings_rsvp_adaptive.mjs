import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
    createRsvpPreviewData,
    normalizeRsvpGuest,
} from "../components/rsvp.js";
import { rsvpPanel } from "../inspector/panels/rsvp.js";

const root = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);

const read = relative => fs.readFileSync(
    path.join(root, relative),
    "utf8",
);

test("J1.1 RSVP preserves person/menu metadata as display-only data", () => {
    const guest = normalizeRsvpGuest({
        id: 10,
        name: "Mateo Pérez",
        personType: "NINO",
        personTypeLabel: "Niño",
        menuType: "INFANTIL",
        menuLabel: "Menú infantil",
        attending: null,
    });

    assert.equal(guest.personTypeLabel, "Niño");
    assert.equal(guest.menuLabel, "Menú infantil");
    assert.equal(guest.attending, null);
});

test("J1.1 RSVP preview includes adult/child and menu examples", () => {
    const preview = createRsvpPreviewData();
    assert.ok(preview.guests.some(guest => guest.personTypeLabel === "Niño"));
    assert.ok(preview.guests.every(guest => guest.menuLabel));
});

test("J1.1 RSVP Inspector exposes visual badges and adaptive density", () => {
    const content = rsvpPanel().find(group => group.id === "rsvp-content");
    const keys = content.fields.map(field => field.key);
    assert.ok(keys.includes("rsvpShowPersonType"));
    assert.ok(keys.includes("rsvpShowMenu"));
    assert.ok(keys.includes("rsvpDensity"));
});

test("J1.1 renderer has compact adaptive roster and internal scroll", () => {
    const renderer = read("renderer/renderer.js");
    const css = read("renderer/renderer.css");
    assert.match(renderer, /data\.guests\.length >= 4/);
    assert.match(renderer, /r3-rsvp__badge/);
    assert.match(css, /overflow-y:\s*auto/);
    assert.match(css, /data-r3-rsvp-density="COMPACT"/);
});

test("J1.1 editor uses bootstrap invitationPreview instead of blank context", () => {
    const demo = read("demo_r3_07.js");
    assert.match(demo, /builderRuntimeContext\.invitationPreview/);
    assert.match(demo, /invitationContext,/);
});
