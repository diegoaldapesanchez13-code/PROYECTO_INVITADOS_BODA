async function copiarLink(linkId) {
    const element = document.getElementById(linkId);
    if (!element) return;

    const value = element.innerText.trim();
    let copied = false;

    try {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(value);
            copied = true;
        }
    } catch (_) {
        copied = false;
    }

    if (!copied) {
        const fallback = document.createElement('textarea');
        fallback.value = value;
        fallback.setAttribute('readonly', '');
        fallback.style.position = 'fixed';
        fallback.style.opacity = '0';
        document.body.append(fallback);
        fallback.select();
        copied = document.execCommand('copy');
        fallback.remove();
    }

    const button = document.querySelector(
        `[data-copy-link-target="${CSS.escape(linkId)}"]`
    );
    if (button) {
        const original = button.textContent;
        button.textContent = copied ? 'Link copiado' : 'No se pudo copiar';
        setTimeout(() => {
            button.textContent = original;
        }, 1600);
    }
}

const tabByTarget = {
    resumen: 'resumen',
    invitacion: 'invitacion',
    personalizacion: 'invitacion',
    diseno: 'invitacion',
    contenido: 'contenido',
    servicios: 'servicios',
    agenda: 'agenda',
    tareas: 'tareas',
    finanzas: 'finanzas',
    documentos: 'documentos',
    invitados: 'invitados',
    operacion: 'operacion',
    produccion: 'resumen',
    indicadores: 'resumen',
    graficas: 'resumen',
    usuarios: 'usuarios',
};

function activarTabDashboard(tabName, options = {}) {
    const tabs = document.querySelectorAll('[data-dashboard-tab]');
    const panels = document.querySelectorAll('[data-tab-panel]');
    if (!tabName || !tabs.length || !panels.length) return;

    const exists = Array.from(panels).some(
        (panel) => panel.dataset.tabPanel === tabName
    );
    if (!exists) {
        tabName = 'resumen';
    }

    tabs.forEach((tab) => {
        const active = tab.dataset.dashboardTab === tabName;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-current', active ? 'page' : 'false');
    });

    panels.forEach((panel) => {
        panel.hidden = panel.dataset.tabPanel !== tabName;
    });

    localStorage.setItem('dashboardTab', tabName);

    if (options.updateHash !== false) {
        const nextHash = `#${tabName}`;
        if (window.location.hash !== nextHash) {
            history.replaceState(null, '', nextHash);
        }
    }

    if (tabName === 'resumen') {
        requestAnimationFrame(() => {
            cargarGraficasDashboard().catch(() => {});
        });
    }
}

function activarTabDesdeHash() {
    const target = window.location.hash.replace('#', '');
    const tab = tabByTarget[target];
    if (!tab) return false;

    activarTabDashboard(tab, { updateHash: false });
    return true;
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


function enableGuestWorkspaceControls() {
    const syncExtraToggle = (toggle) => {
        const form = toggle.closest('form');
        const field = form?.querySelector('[data-guest-extra-count]');
        const input = field?.querySelector('input[name="cantidad_extra_permitida"]');
        if (!field) return;
        field.hidden = !toggle.checked;
        if (!toggle.checked && input) input.value = '0';
    };

    document.querySelectorAll('[data-guest-extra-toggle]').forEach((toggle) => {
        if (toggle.dataset.guestToggleReady) return;
        toggle.dataset.guestToggleReady = 'true';
        toggle.addEventListener('change', () => syncExtraToggle(toggle));
        syncExtraToggle(toggle);
    });

    document.querySelectorAll('[data-guest-create-form]').forEach((form) => {
        const type = form.querySelector('[data-guest-group-type]');
        const members = form.querySelector('[data-family-members]');
        const nameLabel = form.querySelector('[data-guest-name-label]');
        if (!type || type.dataset.guestTypeReady) return;
        type.dataset.guestTypeReady = 'true';

        const syncType = () => {
            const familiar = type.value === 'FAMILIAR';
            if (members) members.hidden = !familiar;
            if (nameLabel) {
                nameLabel.textContent = familiar
                    ? 'Nombre del grupo familiar'
                    : 'Nombre de la persona';
            }
        };

        type.addEventListener('change', syncType);
        syncType();
    });
}


function openOperationSubpanel(target) {
    if (!target) return;

    activarTabDashboard('operacion');

    const scope = document.querySelector(
        '[data-subnav-scope="operacion-evento"]'
    );
    if (!scope) return;

    activateSubpanel(scope, target);
    requestAnimationFrame(() => {
        scope.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    enablePasswordToggles();
    enablePreviewRefresh();
    enableGuestWorkspaceControls();

    document.querySelectorAll('[data-dashboard-tab]').forEach((tab) => {
        tab.addEventListener('click', () => {
            const operationTarget =
                tab.dataset.openOperationSubpanel;
            if (operationTarget) {
                openOperationSubpanel(operationTarget);
                return;
            }
            activarTabDashboard(
                tab.dataset.dashboardTab
            );
        });
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
        activarTabDashboard(localStorage.getItem('dashboardTab') || 'resumen');
    }

    window.addEventListener('hashchange', activarTabDesdeHash);
});
