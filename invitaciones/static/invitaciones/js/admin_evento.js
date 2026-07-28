(function () {
    function rowFor(fieldName) {
        return document.querySelector('.form-row.field-' + fieldName);
    }

    function toggleCustomColors() {
        var selector = document.getElementById('id_paleta_colores');
        if (!selector) return;

        var showCustom = selector.value === 'PERSONALIZADA';
        ['color_principal', 'color_secundario', 'color_acento'].forEach(function (fieldName) {
            var row = rowFor(fieldName);
            if (row) row.style.display = showCustom ? '' : 'none';
        });
    }

    function addLiveFilePreviews() {
        var names = [
            'foto_portada',
            'logo_portada',
            'sello_sobre',
            'dress_code_permitido_imagen',
            'dress_code_prohibido_imagen',
            'fondo_invitacion',
            'fondo_cuenta_regresiva',
            'fondo_detalles',
            'fondo_album',
            'fondo_menu',
            'fondo_regalos',
            'fondo_rsvp'
        ];

        names.forEach(function (fieldName) {
            var input = document.getElementById('id_' + fieldName);
            if (!input) return;

            input.addEventListener('change', function () {
                var file = input.files && input.files[0];
                var oldPreview = input.parentNode.querySelector('.admin-live-preview');
                if (oldPreview) oldPreview.remove();
                if (!file || !file.type || file.type.indexOf('image/') !== 0) return;

                var img = document.createElement('img');
                img.className = 'admin-live-preview';
                img.alt = 'Preview';
                img.src = URL.createObjectURL(file);
                input.insertAdjacentElement('afterend', img);
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var selector = document.getElementById('id_paleta_colores');
        if (selector) {
            selector.addEventListener('change', toggleCustomColors);
            toggleCustomColors();
        }
        addLiveFilePreviews();
    });
})();
