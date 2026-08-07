(function () {
    function rowFor(fieldName) {
        return document.querySelector('.form-row.field-' + fieldName);
    }

    function findGuestsInline() {
        return document.getElementById('invitados-group')
            || document.getElementById('invitado_set-group')
            || document.querySelector('[id$="-group"][id*="invitado"]');
    }

    function ensureNote(target, text) {
        if (!target || target.querySelector('.admin-dynamic-note')) return;

        var note = document.createElement('div');
        note.className = 'admin-dynamic-note';
        note.textContent = text;
        target.insertBefore(note, target.firstChild);
    }

    function toggleInviteType() {
        var selector = document.getElementById('id_tipo');
        if (!selector) return;

        var personal = selector.value === 'PERSONAL';
        var personalFields = [
            'cantidad_extra_permitida',
            'asistira',
            'acompanantes_adultos',
            'acompanantes_ninos',
            'cantidad_confirmada'
        ];
        var guestInline = findGuestsInline();

        personalFields.forEach(function (fieldName) {
            var row = rowFor(fieldName);
            if (row) row.style.display = personal ? '' : 'none';
        });

        if (guestInline) {
            guestInline.style.display = personal ? 'none' : '';
            if (!personal) {
                ensureNote(
                    guestInline,
                    'Agrega aqui cada integrante de la familia para que cada uno confirme si asistira.'
                );
            }
        }

        var maxRow = rowFor('cantidad_maxima');
        if (maxRow) {
            ensureNote(
                maxRow,
                personal
                    ? 'Invitacion personal: el invitado principal cuenta como 1 lugar; agrega acompanantes permitidos solo con numeros.'
                    : 'Invitacion familiar: usa los nombres de abajo para controlar adultos, ninos, mesas y asistencia.'
            );
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var selector = document.getElementById('id_tipo');
        if (selector) {
            selector.addEventListener('change', toggleInviteType);
            toggleInviteType();
        }
    });
})();
