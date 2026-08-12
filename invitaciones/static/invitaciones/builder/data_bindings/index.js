export const DATA_BINDING_SOURCES = Object.freeze({
    MANUAL: "MANUAL",
    EVENT: "EVENT",
    INVITATION_GROUP: "INVITATION_GROUP",
});

export const EVENT_BINDING_FIELDS = Object.freeze([
    ["eventName", "Nombre del evento"],
    ["primaryName", "Nombre principal"],
    ["secondaryName", "Nombre secundario"],
    ["participantNames", "Nombres del evento"],
    ["ceremonyPlace", "Lugar de ceremonia"],
    ["receptionPlace", "Lugar de recepción"],
    ["ceremonyDateText", "Fecha de ceremonia"],
    ["ceremonyTimeText", "Hora de ceremonia"],
    ["receptionDateText", "Fecha de recepción"],
    ["receptionTimeText", "Hora de recepción"],
]);

// Kept for backward compatibility with J.1 documents.
// J.1.2 no longer exposes these fields in the generic Text Inspector because
// RSVP is the canonical UI for invitation/group/person data.
export const INVITATION_BINDING_FIELDS = Object.freeze([
    ["groupName", "Nombre de invitación / familia"],
    ["groupTypeLabel", "Tipo de invitación"],
    ["totalGuests", "Personas invitadas"],
    ["confirmedGuests", "Personas confirmadas"],
    ["pendingGuests", "Personas pendientes"],
]);

export function resolveDataBoundText(
    binding,
    {
        eventContext = {},
        invitationContext = {},
        fallback = "",
    } = {},
) {
    const source = String(
        binding?.source
        || DATA_BINDING_SOURCES.MANUAL
    ).toUpperCase();
    const field = String(
        binding?.field || ""
    ).trim();

    if (
        source === DATA_BINDING_SOURCES.MANUAL
        || !field
    ) {
        return String(fallback ?? "");
    }

    const context =
        source === DATA_BINDING_SOURCES.EVENT
            ? eventContext
            : source
                === DATA_BINDING_SOURCES.INVITATION_GROUP
                ? invitationContext
                : null;

    if (!context) {
        return String(fallback ?? "");
    }

    const value = context[field];

    if (
        value === null
        || value === undefined
        || value === ""
    ) {
        return String(fallback ?? "");
    }

    return String(value);
}

export function defaultFieldForSource(source) {
    if (source === DATA_BINDING_SOURCES.EVENT) {
        return EVENT_BINDING_FIELDS[0][0];
    }
    if (
        source
        === DATA_BINDING_SOURCES.INVITATION_GROUP
    ) {
        return INVITATION_BINDING_FIELDS[0][0];
    }
    return "";
}
