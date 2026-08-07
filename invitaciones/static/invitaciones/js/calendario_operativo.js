document.addEventListener('DOMContentLoaded', () => {
    const calendarElement = document.getElementById('calendar');
    if (!calendarElement || !window.FullCalendar) return;

    const calendar = new FullCalendar.Calendar(calendarElement, {
        locale: 'es',
        initialView: window.innerWidth < 760 ? 'listWeek' : 'dayGridMonth',
        height: 'auto',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,listWeek',
        },
        buttonText: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            list: 'Lista',
        },
        events: calendarElement.dataset.eventsUrl,
        eventClick(info) {
            if (info.event.url) {
                info.jsEvent.preventDefault();
                window.open(info.event.url, '_blank', 'noopener');
            }
        },
        eventDidMount(info) {
            const props = info.event.extendedProps || {};
            const detail = [
                props.tipo,
                props.estado,
                props.categoria,
                props.ubicacion,
                props.responsable ? `Resp: ${props.responsable}` : '',
                props.proveedor ? `Prov: ${props.proveedor}` : '',
            ].filter(Boolean).join(' · ');

            if (detail) {
                info.el.setAttribute('title', detail);
            }
        },
    });

    calendar.render();
});
