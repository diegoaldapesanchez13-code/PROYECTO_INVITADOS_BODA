export const RSVP_STATUS = Object.freeze({
    PENDING: "PENDING",
    ATTENDING: "ATTENDING",
    NOT_ATTENDING: "NOT_ATTENDING",
});

export function createRsvpPreviewData(overrides = {}) {
    return normalizeRsvpData({
        invitationId: "preview-invitation",
        groupName: "Familia Aldape Sánchez",
        guests: [
            {
                id: "preview-1",
                name: "Diego Aldape",
                attending: null,
                personType: "ADULTO",
                personTypeLabel: "Adulto",
                menuType: "ADULTO",
                menuLabel: "Menú adulto",
            },
            {
                id: "preview-2",
                name: "Fernanda Flores",
                attending: true,
                personType: "ADULTO",
                personTypeLabel: "Adulto",
                menuType: "ADULTO",
                menuLabel: "Menú adulto",
            },
            {
                id: "preview-3",
                name: "Mateo",
                attending: null,
                personType: "NINO",
                personTypeLabel: "Niño",
                menuType: "INFANTIL",
                menuLabel: "Menú infantil",
            },
        ],
        ...overrides,
    });
}

export function normalizeRsvpGuest(value = {}, index = 0) {
    const attending = value.attending === true
        ? true
        : value.attending === false
            ? false
            : null;

    return {
        id: String(value.id ?? value.guestId ?? `guest-${index + 1}`),
        name: String(value.name || value.nombre || `Invitado ${index + 1}`).trim() || `Invitado ${index + 1}`,
        attending,
        personType: String(
            value.personType
            || value.tipoPersona
            || ""
        ).trim(),
        personTypeLabel: String(
            value.personTypeLabel
            || value.tipoPersonaLabel
            || ""
        ).trim(),
        menuType: String(
            value.menuType
            || value.tipoMenu
            || ""
        ).trim(),
        menuLabel: String(
            value.menuLabel
            || value.menu
            || ""
        ).trim(),
        extraCompanion: Boolean(
            value.extraCompanion
            ?? value.esAcompananteExtra
            ?? false
        ),
        status: attending === true
            ? RSVP_STATUS.ATTENDING
            : attending === false
                ? RSVP_STATUS.NOT_ATTENDING
                : RSVP_STATUS.PENDING,
    };
}

export function normalizeRsvpData(value = {}) {
    const rawGuests = Array.isArray(value.guests) ? value.guests : [];
    const guests = rawGuests.map((guest, index) => normalizeRsvpGuest(guest, index));

    return {
        invitationId: String(value.invitationId || value.uuid || "").trim(),
        groupName: String(value.groupName || value.nombreGrupo || "Invitado").trim() || "Invitado",
        groupType: String(value.groupType || value.tipoGrupo || "").trim(),
        guests,
        totalGuests: guests.length,
        confirmedGuests: guests.filter(guest => guest.attending === true).length,
        respondedGuests: guests.filter(guest => guest.attending !== null).length,
        pendingGuests: guests.filter(guest => guest.attending === null).length,
    };
}

export function buildRsvpSubmission(form = {}, data = {}) {
    const attendingRaw = form.attending ?? form.asistira ?? null;
    const attending = attendingRaw === true || attendingRaw === "yes" || attendingRaw === "SI"
        ? true
        : attendingRaw === false || attendingRaw === "no" || attendingRaw === "NO"
            ? false
            : null;

    return {
        invitationId: String(data.invitationId || "").trim(),
        guestId: String(form.guestId ?? form.invitadoId ?? "").trim(),
        attending,
    };
}

export function resolveInvitationId(context = {}) {
    const direct = context.invitationId || context.uuid || context.codigo;
    if (direct) return String(direct);

    const pathname = String(context.pathname || globalThis.location?.pathname || "");
    const match = pathname.match(/\/invitacion\/([0-9a-f-]{8,})\/?/i);
    return match?.[1] || "";
}
