import assert from "node:assert/strict";
import { createRsvpPreviewData, normalizeRsvpData, buildRsvpSubmission, resolveInvitationId } from "../components/rsvp.js";

const preview = createRsvpPreviewData();
assert.equal(preview.groupName, "Familia Aldape Sánchez");
assert.equal(normalizeRsvpData({ cantidadMaxima: 4, cantidadConfirmada: 9 }).confirmedGuests, 4);
assert.equal(normalizeRsvpData({ nombreGrupo: "Familia Demo" }).groupName, "Familia Demo");
assert.deepEqual(buildRsvpSubmission({ attending: "no", confirmedGuests: 3 }, { invitationId: "abc", maxGuests: 4 }), {
    invitationId: "abc",
    attending: false,
    confirmedGuests: 0,
    comment: "",
});
assert.equal(resolveInvitationId({ pathname: "/invitacion/4f38f4d9-82d0-4623-874a-401b3574671a/" }), "4f38f4d9-82d0-4623-874a-401b3574671a");
console.log("test_r3_rsvp_component: ok");
