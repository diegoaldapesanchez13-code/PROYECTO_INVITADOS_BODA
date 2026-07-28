function activateRolePanel(targetId) {
    const panels = document.querySelectorAll('[data-role-panel]');
    const links = document.querySelectorAll('[data-role-link]');
    if (!targetId || !panels.length) return;

    panels.forEach((panel) => {
        panel.hidden = panel.id !== targetId;
    });

    links.forEach((link) => {
        link.classList.toggle('is-active', link.getAttribute('href') === `#${targetId}`);
    });

    localStorage.setItem('roleDashboardPanel', targetId);
}

function activateRolePanelFromHash() {
    const targetId = window.location.hash.replace('#', '');
    const panel = document.getElementById(targetId);
    if (!panel || !panel.matches('[data-role-panel]')) return false;
    activateRolePanel(targetId);
    return true;
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

document.addEventListener('DOMContentLoaded', () => {
    enablePasswordToggles();

    document.querySelectorAll('[data-role-link]').forEach((link) => {
        link.addEventListener('click', () => {
            activateRolePanel(link.getAttribute('href').replace('#', ''));
        });
    });

    if (!activateRolePanelFromHash()) {
        const saved = localStorage.getItem('roleDashboardPanel');
        const firstPanel = document.querySelector('[data-role-panel]');
        activateRolePanel(document.getElementById(saved) ? saved : firstPanel?.id);
    }

    window.addEventListener('hashchange', activateRolePanelFromHash);

    document.querySelectorAll('[data-filter-scope]').forEach((scope) => {
        scope.querySelectorAll('[data-filter-search], [data-filter-field]').forEach((control) => {
            control.addEventListener('input', () => applyScopedFilters(scope));
            control.addEventListener('change', () => applyScopedFilters(scope));
        });
        applyScopedFilters(scope);
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

    document.querySelectorAll('form[data-confirm]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
});
