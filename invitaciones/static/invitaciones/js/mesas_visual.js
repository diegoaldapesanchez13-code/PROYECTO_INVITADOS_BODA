function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(value, max));
}

function setStatus(message) {
    const status = document.getElementById('floorplanStatus');
    if (status) status.textContent = message;
}

function collectPositions() {
    return Array.from(document.querySelectorAll('.floor-table')).map((table) => ({
        id: table.dataset.tableId,
        x: Math.round(parseFloat(table.style.left || '0')),
        y: Math.round(parseFloat(table.style.top || '0')),
        ancho: Math.round(table.offsetWidth),
        alto: Math.round(table.offsetHeight),
    }));
}

async function saveFloorplan() {
    const panel = document.querySelector('.floorplan-panel');
    if (!panel) return;

    const payload = new FormData();
    payload.append('evento_id', panel.dataset.eventId);
    payload.append('posiciones', JSON.stringify(collectPositions()));

    setStatus('Guardando acomodo...');
    const response = await fetch(panel.dataset.saveUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: payload,
    });

    if (!response.ok) {
        setStatus('No se pudo guardar. Revisa la conexion e intenta otra vez.');
        return;
    }

    const data = await response.json();
    setStatus(`Acomodo guardado: ${data.mesas_actualizadas} mesa(s).`);
}

function autoArrangeTables() {
    const stage = document.getElementById('floorplanStage');
    if (!stage) return;

    const tables = Array.from(stage.querySelectorAll('.floor-table'));
    const gap = 22;
    const width = stage.clientWidth;
    let x = gap;
    let y = gap;
    let rowHeight = 0;

    tables.forEach((table) => {
        const tableWidth = table.offsetWidth || Number(table.dataset.width) || 140;
        const tableHeight = table.offsetHeight || Number(table.dataset.height) || 140;

        if (x + tableWidth + gap > width) {
            x = gap;
            y += rowHeight + gap;
            rowHeight = 0;
        }

        table.style.left = `${x}px`;
        table.style.top = `${y}px`;
        x += tableWidth + gap;
        rowHeight = Math.max(rowHeight, tableHeight);
    });

    setStatus('Mesas ordenadas. Guarda para conservar esta distribucion.');
}

function enableDragging() {
    const stage = document.getElementById('floorplanStage');
    if (!stage) return;

    stage.querySelectorAll('.floor-table').forEach((table) => {
        table.addEventListener('pointerdown', (event) => {
            table.setPointerCapture(event.pointerId);
            table.classList.add('is-moving');

            const stageRect = stage.getBoundingClientRect();
            const tableRect = table.getBoundingClientRect();
            const offsetX = event.clientX - tableRect.left;
            const offsetY = event.clientY - tableRect.top;

            const moveTable = (moveEvent) => {
                const x = clamp(
                    moveEvent.clientX - stageRect.left - offsetX + stage.scrollLeft,
                    0,
                    stage.scrollWidth - table.offsetWidth,
                );
                const y = clamp(
                    moveEvent.clientY - stageRect.top - offsetY + stage.scrollTop,
                    0,
                    stage.scrollHeight - table.offsetHeight,
                );
                table.style.left = `${x}px`;
                table.style.top = `${y}px`;
                setStatus('Hay cambios sin guardar.');
            };

            const stopDragging = () => {
                table.classList.remove('is-moving');
                table.removeEventListener('pointermove', moveTable);
                table.removeEventListener('pointerup', stopDragging);
                table.removeEventListener('pointercancel', stopDragging);
            };

            table.addEventListener('pointermove', moveTable);
            table.addEventListener('pointerup', stopDragging);
            table.addEventListener('pointercancel', stopDragging);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    enableDragging();

    const saveButton = document.getElementById('saveFloorplan');
    if (saveButton) {
        saveButton.addEventListener('click', () => {
            saveFloorplan().catch(() => {
                setStatus('No se pudo guardar. Intenta otra vez.');
            });
        });
    }

    const resetButton = document.getElementById('resetFloorplan');
    if (resetButton) {
        resetButton.addEventListener('click', autoArrangeTables);
    }

    document.querySelectorAll('form[data-confirm]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
});
