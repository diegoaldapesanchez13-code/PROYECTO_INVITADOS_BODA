document.addEventListener('DOMContentLoaded', () => {
    const calendarElement = document.getElementById('calendar');
    if (!calendarElement || !window.FullCalendar) return;

    const calendar = new FullCalendar.Calendar(calendarElement, {
        locale: 'es',
        initialView: window.innerWidth < 760 ? 'listWeek' : 'timeGridWeek',
        height: 'auto',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
        },
        buttonText: {
            today: 'Hoy',
            month: 'Mes',
            week: 'Semana',
            day: 'Dia',
            list: 'Agenda',
        },
        nowIndicator: true,
        allDaySlot: true,
        slotMinTime: '06:00:00',
        slotMaxTime: '24:00:00',
        slotDuration: '00:30:00',
        eventTimeFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
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
                props.descripcion || '',
            ].filter(Boolean).join(' · ');

            if (detail) {
                info.el.setAttribute('title', detail);
            }
        },
    });

    calendar.render();
});
