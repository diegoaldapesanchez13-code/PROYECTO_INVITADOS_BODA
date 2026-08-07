function copiarLink(linkId) {
    const element = document.getElementById(linkId);
    if (!element) return;

    navigator.clipboard.writeText(element.innerText.trim());
}

const tabByTarget = {
    personalizacion: 'diseno',
    operacion: 'contenido',
    indicadores: 'operacion',
    produccion: 'operacion',
    graficas: 'operacion',
    invitados: 'invitados',
    usuarios: 'usuarios',
};

function activarTabDashboard(tabName) {
    const tabs = document.querySelectorAll('[data-dashboard-tab]');
    const panels = document.querySelectorAll('[data-tab-panel]');
    if (!tabName || !tabs.length || !panels.length) return;

    tabs.forEach((tab) => {
        tab.classList.toggle('active', tab.dataset.dashboardTab === tabName);
    });

    panels.forEach((panel) => {
        panel.hidden = panel.dataset.tabPanel !== tabName;
    });

    localStorage.setItem('dashboardTab', tabName);

    if (tabName === 'operacion') {
        cargarGraficasDashboard().catch(() => {});
    }
}

function activarTabDesdeHash() {
    const target = window.location.hash.replace('#', '');
    if (tabByTarget[target]) {
        activarTabDashboard(tabByTarget[target]);
        setTimeout(() => {
            document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 40);
        return true;
    }
    return false;
}

function crearGrafica(canvasId, tipo, labels, values, colors) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;

    const existingChart = Chart.getChart ? Chart.getChart(canvas) : null;
    if (existingChart) {
        existingChart.destroy();
    }

    new Chart(canvas, {
        type: tipo,
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: colors,
                borderWidth: 1,
                borderRadius: tipo === 'bar' ? 6 : 0,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 10,
                        usePointStyle: true,
                    },
                },
            },
            scales: tipo === 'bar' ? {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                    },
                },
            } : {},
        },
    });
}

async function cargarGraficasDashboard() {
    const panel = document.querySelector('[data-metrics-url]');
    if (!panel || !panel.dataset.metricsUrl || !window.Chart) return;

    const response = await fetch(panel.dataset.metricsUrl);
    if (!response.ok) return;

    const data = await response.json();
    const charts = data.charts || {};
    const palette = ['#2f7a4d', '#d2b074', '#9b4d36', '#52627d', '#93a79b'];

    if (charts.invitados) {
        crearGrafica('chartInvitados', 'doughnut', charts.invitados.labels, charts.invitados.values, palette);
    }
    if (charts.buffet) {
        crearGrafica('chartBuffet', 'doughnut', charts.buffet.labels, charts.buffet.values, ['#2f7a4d', '#d2b074']);
    }
    if (charts.presupuesto) {
        crearGrafica('chartPresupuesto', 'bar', charts.presupuesto.labels, charts.presupuesto.values, palette);
    }
    if (charts.tareas) {
        crearGrafica('chartTareas', 'bar', charts.tareas.labels, charts.tareas.values, palette);
    }
    if (charts.proveedores) {
        crearGrafica('chartProveedores', 'bar', charts.proveedores.labels, charts.proveedores.values, palette);
    }
}

function enablePasswordToggles() {
    document.querySelectorAll('input[type="password"][name="password_usuario"]').forEach((input) => {
        if (input.dataset.toggleReady) return;
        input.dataset.toggleReady = 'true';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'password-toggle';
        button.textContent = 'Mostrar';
        button.addEventListener('click', () => {
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            button.textContent = isHidden ? 'Ocultar' : 'Mostrar';
        });

        input.insertAdjacentElement('afterend', button);
    });
}

function activateSubpanel(scope, target) {
    const panels = Array.from(scope.querySelectorAll('[data-subpanel]'));
    const buttons = Array.from(scope.querySelectorAll('[data-subpanel-button]'));
    if (!target || !panels.length) return;

    panels.forEach((panel) => {
        panel.hidden = panel.dataset.subpanel !== target;
    });
    buttons.forEach((button) => {
        button.classList.toggle('is-active', button.dataset.subpanelButton === target);
    });

    const key = scope.dataset.subnavScope ? `subpanel:${scope.dataset.subnavScope}` : null;
    if (key) {
        localStorage.setItem(key, target);
    }
}

function normalizeFilterText(value) {
    return (value || '')
        .toString()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();
}

function applyScopedFilters(scope) {
    const search = normalizeFilterText(scope.querySelector('[data-filter-search]')?.value);
    const selects = Array.from(scope.querySelectorAll('[data-filter-field]'));
    const items = Array.from(scope.querySelectorAll('[data-filter-item]'));
    let visibleCount = 0;

    items.forEach((item) => {
        const searchable = normalizeFilterText(item.dataset.search || item.textContent);
        const matchesSearch = !search || searchable.includes(search);
        const matchesSelects = selects.every((select) => {
            const selectedValue = select.value;
            if (!selectedValue) return true;
            const field = select.dataset.filterField;
            return item.dataset[field] === selectedValue;
        });
        const isVisible = matchesSearch && matchesSelects;
        item.hidden = !isVisible;
        if (isVisible) visibleCount += 1;
    });

    const counter = scope.querySelector('[data-filter-count]');
    if (counter) {
        counter.textContent = `${visibleCount} visible${visibleCount === 1 ? '' : 's'}`;
    }
    scope.classList.toggle('is-empty-filter', items.length > 0 && visibleCount === 0);
}

function enablePreviewRefresh() {
    document.querySelectorAll('[data-preview-refresh]').forEach((button) => {
        if (button.dataset.previewReady) return;
        button.dataset.previewReady = 'true';
        button.addEventListener('click', () => {
            const panel = button.closest('.live-preview-panel');
            const frame = panel?.querySelector('[data-preview-frame]');
            if (!frame) return;
            const url = new URL(frame.src, window.location.href);
            url.searchParams.set('_preview_ts', Date.now().toString());
            frame.src = url.toString();
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    enablePasswordToggles();
    enablePreviewRefresh();

    document.querySelectorAll('[data-dashboard-tab]').forEach((tab) => {
        tab.addEventListener('click', () => activarTabDashboard(tab.dataset.dashboardTab));
    });

    document.querySelectorAll('form[data-confirm]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll('[data-subnav-scope]').forEach((scope) => {
        const key = scope.dataset.subnavScope ? `subpanel:${scope.dataset.subnavScope}` : null;
        const saved = key ? localStorage.getItem(key) : null;
        const firstButton = scope.querySelector('[data-subpanel-button]');
        const initial = scope.querySelector(`[data-subpanel="${saved}"]`) ? saved : firstButton?.dataset.subpanelButton;

        scope.querySelectorAll('[data-subpanel-button]').forEach((button) => {
            button.addEventListener('click', () => activateSubpanel(scope, button.dataset.subpanelButton));
        });
        activateSubpanel(scope, initial);
    });

    document.querySelectorAll('[data-filter-scope]').forEach((scope) => {
        scope.querySelectorAll('[data-filter-search], [data-filter-field]').forEach((control) => {
            control.addEventListener('input', () => applyScopedFilters(scope));
            control.addEventListener('change', () => applyScopedFilters(scope));
        });
        applyScopedFilters(scope);
    });

    document.querySelectorAll('a[href^="#"]').forEach((link) => {
        link.addEventListener('click', () => {
            const target = link.getAttribute('href').replace('#', '');
            if (tabByTarget[target]) {
                activarTabDashboard(tabByTarget[target]);
            }
        });
    });

    if (!activarTabDesdeHash()) {
        activarTabDashboard(localStorage.getItem('dashboardTab') || 'diseno');
    }

    window.addEventListener('hashchange', activarTabDesdeHash);
});
