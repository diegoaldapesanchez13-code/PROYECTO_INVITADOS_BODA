export const RSVP_STATUS = Object.freeze({
    PENDING: "PENDING",
    ATTENDING: "ATTENDING",
    NOT_ATTENDING: "NOT_ATTENDING",
});

export function createRsvpPreviewData(overrides = {}) {
    return {
        invitationId: "preview-invitation",
        groupName: "Familia Aldape Sánchez",
        maxGuests: 4,
        attending: null,
        confirmedGuests: 2,
        comment: "",
        status: RSVP_STATUS.PENDING,
        ...overrides,
    };
}

export function normalizeRsvpData(value = {}) {
    const maxGuests = clampInteger(value.maxGuests ?? value.cantidadMaxima ?? 1, 1, 50);
    const confirmedGuests = clampInteger(value.confirmedGuests ?? value.cantidadConfirmada ?? 1, 0, maxGuests);
    const attending = value.attending === true
        ? true
        : value.attending === false
            ? false
            : null;

    return {
        invitationId: String(value.invitationId || value.uuid || "").trim(),
        groupName: String(value.groupName || value.nombreGrupo || "Invitado").trim() || "Invitado",
        maxGuests,
        confirmedGuests,
        attending,
        comment: String(value.comment || value.comentario || ""),
        status: attending === true
            ? RSVP_STATUS.ATTENDING
            : attending === false
                ? RSVP_STATUS.NOT_ATTENDING
                : RSVP_STATUS.PENDING,
    };
}

export function buildRsvpSubmission(form, data = {}) {
    const attendingRaw = form?.attending ?? form?.asistira ?? null;
    const attending = attendingRaw === true || attendingRaw === "yes" || attendingRaw === "SI"
        ? true
        : attendingRaw === false || attendingRaw === "no" || attendingRaw === "NO"
            ? false
            : null;
    const maxGuests = clampInteger(data.maxGuests ?? 1, 1, 50);

    return {
        invitationId: String(data.invitationId || "").trim(),
        attending,
        confirmedGuests: attending === true
            ? clampInteger(form?.confirmedGuests ?? form?.cantidadConfirmada ?? 1, 1, maxGuests)
            : 0,
        comment: String(form?.comment ?? form?.comentario ?? "").trim(),
    };
}

export function resolveInvitationId(context = {}) {
    const direct = context.invitationId || context.uuid || context.codigo;
    if (direct) return String(direct);

    const pathname = String(context.pathname || globalThis.location?.pathname || "");
    const match = pathname.match(/\/invitacion\/([0-9a-f-]{8,})\/?/i);
    return match?.[1] || "";
}

function clampInteger(value, min, max) {
    const number = Number.parseInt(value, 10);
    if (!Number.isFinite(number)) return min;
    return Math.min(Math.max(number, min), max);
}
