import assert from "node:assert/strict";

import {
    buildRsvpSubmission,
    createRsvpPreviewData,
    normalizeRsvpData,
} from "../components/rsvp.js";

const preview = createRsvpPreviewData();

assert.ok(Array.isArray(preview.guests));
assert.ok(preview.guests.length >= 2);
assert.equal(preview.maxGuests, undefined);
assert.equal(preview.confirmedGuests, 1);
assert.equal(preview.respondedGuests, 1);
assert.equal(preview.pendingGuests, preview.guests.length - 1);

const normalized = normalizeRsvpData({
    invitationId: "family-uuid",
    groupName: "Familia Pérez",
    guests: [
        { id: 101, name: "Ana", attending: true },
        { id: 102, name: "Luis", attending: null },
        { id: 103, name: "Sofía", attending: false },
    ],
});

assert.equal(normalized.invitationId, "family-uuid");
assert.equal(normalized.groupName, "Familia Pérez");
assert.equal(normalized.totalGuests, 3);
assert.equal(normalized.confirmedGuests, 1);
assert.equal(normalized.respondedGuests, 2);
assert.equal(normalized.pendingGuests, 1);
assert.equal(normalized.guests[0].name, "Ana");
assert.equal(normalized.guests[1].attending, null);
assert.equal(normalized.guests[2].attending, false);

const submission = buildRsvpSubmission(
    {
        guestId: 102,
        attending: "yes",
        confirmedGuests: 4,
        comment: "legacy field must not be submitted",
    },
    normalized,
);

assert.deepEqual(submission, {
    invitationId: "family-uuid",
    guestId: "102",
    attending: true,
});
assert.equal("confirmedGuests" in submission, false);
assert.equal("comment" in submission, false);

console.log("test_r3_rsvp_component: individual RSVP V2 ok");
