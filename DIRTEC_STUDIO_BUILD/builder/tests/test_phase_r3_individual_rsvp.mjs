import assert from "node:assert/strict";
import test from "node:test";

import {
    buildRsvpSubmission,
    createRsvpPreviewData,
    normalizeRsvpData,
} from "../components/rsvp.js";

test("R3 RSVP normalizes an individual roster", () => {
    const data = normalizeRsvpData({
        invitationId: "abc",
        groupName: "Familia Pérez",
        guests: [
            { id: 10, name: "Ana", attending: true },
            { id: 11, name: "Luis", attending: null },
            { id: 12, name: "Sofía", attending: false },
        ],
    });

    assert.equal(data.totalGuests, 3);
    assert.equal(data.confirmedGuests, 1);
    assert.equal(data.respondedGuests, 2);
    assert.equal(data.pendingGuests, 1);
    assert.equal(data.guests[1].name, "Luis");
});

test("R3 RSVP submission only carries guest identity and attendance", () => {
    const payload = buildRsvpSubmission(
        { guestId: 11, attending: "yes", confirmedGuests: 99, comment: "ignored" },
        { invitationId: "abc" },
    );

    assert.deepEqual(payload, {
        invitationId: "abc",
        guestId: "11",
        attending: true,
    });
    assert.equal("confirmedGuests" in payload, false);
    assert.equal("comment" in payload, false);
});

test("R3 RSVP preview is person based", () => {
    const preview = createRsvpPreviewData();
    assert.ok(preview.guests.length >= 2);
    assert.equal(preview.maxGuests, undefined);
    assert.equal(preview.comment, undefined);
});
