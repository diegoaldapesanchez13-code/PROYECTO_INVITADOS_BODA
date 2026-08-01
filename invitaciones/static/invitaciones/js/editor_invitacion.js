(function () {
    const root = document.querySelector('.editor-shell');
    const configNode = document.getElementById('editor-config');
    const contentNode = document.getElementById('editor-content');
    const guestsNode = document.getElementById('editor-guests');
    const versionsNode = document.getElementById('editor-versions');
    if (!root || !configNode) return;

    const paletteMap = {
        BOSQUE: ['#263126', '#f6f7f3', '#2f7a4d', '#e8f1e7'],
        ROSA: ['#6f3448', '#fff4f6', '#c77d92', '#f9e3ea'],
        TERRACOTA: ['#743d2b', '#fff7f0', '#b85f43', '#f2dfd1'],
        AZUL: ['#1e2b44', '#f4f7fb', '#52627d', '#dce6f2'],
        LAVANDA: ['#50436f', '#fbf8ff', '#8e7eb6', '#ebe3f6'],
        DORADO: ['#5f5134', '#fffaf0', '#c8a96a', '#f5ead1'],
        TINTA_MARFIL: ['#22252d', '#fbf7ef', '#111827', '#ede2d0'],
    };
    const fontMap = {
        CLASICA: ['Playfair Display', 'Montserrat'],
        EDITORIAL: ['Cormorant Garamond', 'Lato'],
        MODERNA: ['Poppins', 'Inter'],
        ROMANTICA: ['Great Vibes', 'Quicksand'],
        MANUSCRITA: ['Allura', 'Montserrat'],
        CURSIVA_ELEGANTE: ['Parisienne', 'Cormorant Garamond'],
    };

    let config = JSON.parse(configNode.textContent || '{}');
    let content = contentNode ? JSON.parse(contentNode.textContent || '{}') : {};
    let guests = guestsNode ? JSON.parse(guestsNode.textContent || '{}') : {};
    let versions = versionsNode ? JSON.parse(versionsNode.textContent || '[]') : [];
    let builderComponents = [];
    let selectedComponentId = null;
    let selectedId = config.sections?.[0]?.sectionId || null;
    let currentDeviceMode = 'iphone';
    let livePreviewMode = 'edit';
    let realPreviewDrag = null;
    let componentTreeDrag = null;
    let currentPreviewMode = root.querySelector('[data-real-preview-frame]')
        ? 'real'
        : 'draft';
    let nativeElementRegistry = [];
    const layerBounds = { min: -40, max: 140 };

    const sectionList = root.querySelector('[data-section-list]');
    const componentTree = root.querySelector('[data-component-tree]');
    const previewRoot = root.querySelector('[data-preview-root]');
    const saveState = root.querySelector('[data-save-state]');
    const sectionProps = root.querySelector('[data-section-properties]');
    const versionList = root.querySelector('[data-version-list]');
    const guestList = root.querySelector('[data-guest-list]');
    const phonePreviews = root.querySelectorAll('.phone-preview');
    const realPreviewFrame = root.querySelector('[data-real-preview-frame]');

    const realContentSections = new Set([
        'DETALLES',
        'REGALOS',
        'ALBUM',
        'ALBUM_COMPARTIDO',
    ]);

    function defaultRealContentConfig(sectionType = '') {
        return {
            enabled: realContentSections.has(sectionType),
            x: 50,
            y: 50,
            width: 100,
            scale: 1,
            rotation: 0,
            opacity: 1,
            zIndex: 5,
            layout: 'grid',
            align: 'center',
            gap: 14,
            cardBg: '#ffffff',
            cardRadius: 0,
            cardPadding: 16,
            cardShadow: false,
            textSize: 15,
            showMedia: true,
            showAddress: true,
            showMaps: true,
            items: {
                ceremony: {
                    visible: true,
                    label: 'Ceremonia',
                    order: 1,
                    showTitle: true,
                    showDate: true,
                    showTime: true,
                    showPlace: true,
                    showMedia: true,
                    showAddress: true,
                    showButton: true,
                    showMaps: true,
                    cardBg: '#ffffff',
                    mediaPosition: 'top',
                    mapDisplay: 'button-map',
                    buttonLabel: 'Ver ubicacion',
                    mapAsset: {},
                },
                reception: {
                    visible: true,
                    label: 'Recepcion',
                    order: 2,
                    showTitle: true,
                    showDate: true,
                    showTime: true,
                    showPlace: true,
                    showMedia: true,
                    showAddress: true,
                    showButton: true,
                    showMaps: true,
                    cardBg: '#ffffff',
                    mediaPosition: 'top',
                    mapDisplay: 'button-map',
                    buttonLabel: 'Ver ubicacion',
                    mapAsset: {},
                },
            },
        };
    }

    function normalizeRealContentConfig(value, sectionType = '') {
        const defaults = defaultRealContentConfig(sectionType);
        const source = value && typeof value === 'object' ? value : {};
        const items = source.items && typeof source.items === 'object' ? source.items : {};
        return {
            ...defaults,
            ...source,
            enabled: realContentSections.has(sectionType) && source.enabled !== false,
            x: clamp(source.x ?? defaults.x, 0, 100),
            y: clamp(source.y ?? defaults.y, 0, 100),
            width: clamp(source.width ?? defaults.width, 35, 120),
            scale: clamp(source.scale ?? defaults.scale, 0.5, 1.8),
            rotation: clamp(source.rotation ?? defaults.rotation, -45, 45),
            opacity: clamp(source.opacity ?? defaults.opacity, 0, 1),
            zIndex: clamp(source.zIndex ?? defaults.zIndex, 1, 30),
            layout: ['grid', 'stack'].includes(source.layout) ? source.layout : defaults.layout,
            align: ['left', 'center', 'right'].includes(source.align) ? source.align : defaults.align,
            gap: clamp(source.gap ?? defaults.gap, 0, 42),
            cardBg: /^#[0-9a-f]{6}$/i.test(source.cardBg || '') ? source.cardBg : defaults.cardBg,
            cardRadius: clamp(source.cardRadius ?? defaults.cardRadius, 0, 28),
            cardPadding: clamp(source.cardPadding ?? defaults.cardPadding, 4, 36),
            textSize: clamp(source.textSize ?? defaults.textSize, 11, 22),
            cardShadow: Boolean(source.cardShadow),
            showMedia: source.showMedia !== false,
            showAddress: source.showAddress !== false,
            showMaps: source.showMaps !== false,
            items: {
                ceremony: {
                    ...defaults.items.ceremony,
                    ...(items.ceremony || {}),
                    visible: items.ceremony?.visible !== false,
                    label: String(items.ceremony?.label || defaults.items.ceremony.label).slice(0, 80),
                    order: clamp(items.ceremony?.order ?? defaults.items.ceremony.order, 0, 20),
                    showTitle: items.ceremony?.showTitle !== false,
                    showDate: items.ceremony?.showDate !== false,
                    showTime: items.ceremony?.showTime !== false,
                    showPlace: items.ceremony?.showPlace !== false,
                    showMedia: items.ceremony?.showMedia !== false,
                    showAddress: items.ceremony?.showAddress !== false,
                    showButton: items.ceremony?.showButton !== false,
                    showMaps: items.ceremony?.showMaps !== false,
                    cardBg: /^#[0-9a-f]{6}$/i.test(items.ceremony?.cardBg || '') ? items.ceremony.cardBg : defaults.items.ceremony.cardBg,
                    mediaPosition: ['top', 'bottom', 'hidden'].includes(items.ceremony?.mediaPosition) ? items.ceremony.mediaPosition : defaults.items.ceremony.mediaPosition,
                    mapDisplay: ['button-map', 'button-only', 'map-only', 'hidden'].includes(items.ceremony?.mapDisplay) ? items.ceremony.mapDisplay : defaults.items.ceremony.mapDisplay,
                    buttonLabel: String(items.ceremony?.buttonLabel || defaults.items.ceremony.buttonLabel).slice(0, 80),
                    mapAsset: items.ceremony?.mapAsset && typeof items.ceremony.mapAsset === 'object' ? items.ceremony.mapAsset : {},
                },
                reception: {
                    ...defaults.items.reception,
                    ...(items.reception || {}),
                    visible: items.reception?.visible !== false,
                    label: String(items.reception?.label || defaults.items.reception.label).slice(0, 80),
                    order: clamp(items.reception?.order ?? defaults.items.reception.order, 0, 20),
                    showTitle: items.reception?.showTitle !== false,
                    showDate: items.reception?.showDate !== false,
                    showTime: items.reception?.showTime !== false,
                    showPlace: items.reception?.showPlace !== false,
                    showMedia: items.reception?.showMedia !== false,
                    showAddress: items.reception?.showAddress !== false,
                    showButton: items.reception?.showButton !== false,
                    showMaps: items.reception?.showMaps !== false,
                    cardBg: /^#[0-9a-f]{6}$/i.test(items.reception?.cardBg || '') ? items.reception.cardBg : defaults.items.reception.cardBg,
                    mediaPosition: ['top', 'bottom', 'hidden'].includes(items.reception?.mediaPosition) ? items.reception.mediaPosition : defaults.items.reception.mediaPosition,
                    mapDisplay: ['button-map', 'button-only', 'map-only', 'hidden'].includes(items.reception?.mapDisplay) ? items.reception.mapDisplay : defaults.items.reception.mapDisplay,
                    buttonLabel: String(items.reception?.buttonLabel || defaults.items.reception.buttonLabel).slice(0, 80),
                    mapAsset: items.reception?.mapAsset && typeof items.reception.mapAsset === 'object' ? items.reception.mapAsset : {},
                },
            },
        };
    }

    function defaultSectionConfig() {
        return {
            textAlign: 'center',
            titleSize: 'medium',
            backgroundOpacity: '1',
            backgroundPosition: 'center center',
            textColor: '',
            showTextTitle: true,
            layoutMode: 'normal',
            keepRealContent: true,
            backgroundAsset: {},
            titleAsset: {},
            backgroundFit: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundX: 50,
            backgroundY: 50,
            backgroundScale: 1,
            backgroundXMobile: 50,
            backgroundYMobile: 50,
            backgroundScaleMobile: 1,
            backgroundXTablet: 50,
            backgroundYTablet: 50,
            backgroundScaleTablet: 1,
            backgroundXDesktop: 50,
            backgroundYDesktop: 50,
            backgroundScaleDesktop: 1,
            backgroundBrightness: 1,
            backgroundBlur: 0,
            sectionHeight: 420,
            layoutAutoHeight: false,
            layoutWidth: 100,
            layoutScale: 1,
            layoutExpanded: true,
            layoutCollapsed: false,
            layoutPaddingX: 20,
            layoutPaddingY: 24,
            layoutMarginBottom: 12,
            layoutMinHeight: 150,
            layoutMaxHeight: 0,
            layoutAspectRatio: '',
            activeLayer: 'background',
            showBackgroundLayer: true,
            showTitleAsset: true,
            titleX: 50,
            titleY: 20,
            titleScale: 1,
            titleOpacity: 1,
            titleVisible: true,
            titleRotation: 0,
            titleLocked: false,
            titleZ: 3,
            titleWidth: 72,
            titleAlign: 'center',
            textX: 50,
            textY: 62,
            textScale: 1,
            textOpacity: 1,
            textVisible: true,
            textRotation: 0,
            textLocked: false,
            textZ: 4,
            textWidth: 88,
            textAlignLayer: 'center',
            decorX: 50,
            decorY: 12,
            decorScale: 1,
            decorOpacity: 0.42,
            decorVisible: false,
            decorRotation: 0,
            decorLocked: false,
            decorZ: 1,
            decorWidth: 36,
            decorAlign: 'center',
            decorStyle: 'line',
            customLayers: [],
        };
    }

    function ensureSectionConfig(section) {
        section.config = { ...defaultSectionConfig(), ...(section.config || {}) };
        section.config.customLayers = ensureCustomLayers(section.config);
        section.config.realContent = normalizeRealContentConfig(section.config.realContent, section.type);
        return section.config;
    }

    function csrfToken() {
        return document.cookie.split('; ')
            .find((row) => row.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }

    function setState(message) {
        if (saveState) saveState.textContent = message;
    }


    function normalizeBuilderComponent(component) {
        const tipo = String(component.tipo || component.type || 'TEXTO').toUpperCase();
        const properties = component.properties && typeof component.properties === 'object' ? component.properties : {};
        return {
            id: Number(component.componentId || component.id || 0),
            sectionId: Number(component.sectionId || 0),
            sectionType: component.sectionType || '',
            tipo: ['TEXTO', 'IMAGEN', 'BOTON'].includes(tipo) ? tipo : 'TEXTO',
            x: Number(component.x ?? 50),
            y: Number(component.y ?? 50),
            width: Number(component.width ?? 44),
            height: Number(component.height ?? 12),
            rotation: Number(component.rotation ?? 0),
            opacity: Number(component.opacity ?? 1),
            zIndex: Number(component.zIndex ?? component.z_index ?? 20),
            locked: Boolean(component.locked),
            hidden: Boolean(component.hidden),
            properties,
        };
    }

    function componentsForSection(section) {
        return builderComponents
            .filter((component) => Number(component.sectionId) === Number(section.sectionId) && !component.hidden)
            .sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0));
    }

    function defaultComponentProperties(tipo, overrides = {}) {
        if (tipo === 'BOTON') return { label: 'Boton', href: '#', style: 'primary', ...overrides };
        if (tipo === 'IMAGEN') return { src: '', alt: 'Imagen', fit: 'contain', ...overrides };
        return { text: 'Nuevo texto', fontSize: 20, fontFamily: 'Playfair Display', color: '', ...overrides };
    }

    function componentPayload(component) {
        return {
            sectionId: component.sectionId,
            tipo: component.tipo,
            x: component.x,
            y: component.y,
            width: component.width,
            height: component.height,
            rotation: component.rotation,
            opacity: component.opacity,
            zIndex: component.zIndex,
            locked: component.locked,
            hidden: component.hidden,
            properties: component.properties || {},
        };
    }

    function componentDetailUrl(component) {
        return `${root.dataset.componentsUrl}${component.id}/`;
    }

    function upsertBuilderComponent(component) {
        const normalized = normalizeBuilderComponent(component);
        const index = builderComponents.findIndex((item) => item.id === normalized.id);
        if (index >= 0) builderComponents[index] = normalized;
        else builderComponents.push(normalized);
        return normalized;
    }

    async function loadBuilderComponents() {
        if (!root.dataset.componentsUrl) return;
        const response = await fetch(root.dataset.componentsUrl, { headers: { 'Accept': 'application/json' } });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudieron cargar componentes.');
        builderComponents = (data.components || []).map(normalizeBuilderComponent);
        renderAll();
    }

    async function createBuilderComponent(tipo, propertyOverrides = {}) {
        const section = selectedSection();
        if (!section) {
            setState('Selecciona una seccion.');
            return null;
        }
        if (!root.dataset.componentsUrl) {
            setState('API de componentes no disponible.');
            return null;
        }
        const component = normalizeBuilderComponent({
            sectionId: section.sectionId,
            sectionType: section.type,
            tipo,
            x: 50,
            y: 50,
            width: tipo === 'BOTON' ? 46 : 52,
            height: tipo === 'TEXTO' ? 10 : 14,
            zIndex: 30,
            properties: defaultComponentProperties(tipo, propertyOverrides),
        });
        setState('Creando componente...');
        const response = await fetch(root.dataset.componentsUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(componentPayload(component)),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo crear el componente.');
        const saved = upsertBuilderComponent(data.component);
        selectedComponentId = saved.id;
        selectedId = saved.sectionId;
        setState('Componente creado');
        renderAll();
        refreshRealPreview();
        return saved;
    }

    async function saveBuilderComponent(component, options = {}) {
        if (!component?.id || !root.dataset.componentsUrl) return;
        const response = await fetch(componentDetailUrl(component), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(componentPayload(component)),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar el componente.');
        const saved = upsertBuilderComponent(data.component);
        Object.assign(component, saved);
        setState('Componente guardado');
        if (options.skipRealRefresh) {
            syncRealPreviewComponent(component);
        } else {
            refreshRealPreview();
        }
    }

    async function deleteBuilderComponent(component) {
        if (!component?.id || !root.dataset.componentsUrl) return;
        setState('Eliminando componente...');
        const response = await fetch(componentDetailUrl(component), {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken(),
            },
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo eliminar el componente.');
        builderComponents = builderComponents.filter((item) => Number(item.id) !== Number(component.id));
        selectedComponentId = null;
        setState('Componente eliminado');
        renderAll();
        refreshRealPreview();
    }

    function componentInnerHtml(component) {
        const props = component.properties || {};
        if (component.tipo === 'BOTON') {
            return `<span class="preview-builder-button ${props.style === 'secondary' ? 'secondary' : ''}">${escapeHtml(props.label || 'Boton')}</span>`;
        }
        if (component.tipo === 'IMAGEN') {
            if (props.src) {
                return `<img class="preview-builder-image" src="${escapeHtml(props.src)}" alt="${escapeHtml(props.alt || 'Imagen')}" style="object-fit:${props.fit === 'cover' ? 'cover' : 'contain'}">`;
            }
            return '<span class="preview-builder-placeholder">Imagen</span>';
        }
        const size = Number(props.fontSize || 20);
        const color = props.color ? `color:${escapeHtml(props.color)};` : '';
        const family = props.fontFamily ? `font-family:${escapeHtml(props.fontFamily)}, serif;` : '';
        return `<span class="preview-builder-text" style="font-size:${size}px;${color}${family}">${escapeHtml(props.text || 'Nuevo texto')}</span>`;
    }

    function setBuilderComponentStyles(element, component) {
        element.style.left = `${component.x}%`;
        element.style.top = `${component.y}%`;
        element.style.width = `${component.width}%`;
        element.style.height = `${component.height}%`;
        element.style.minHeight = `${component.height}%`;
        element.style.transform = `translate(-50%, -50%) rotate(${component.rotation}deg)`;
        element.style.opacity = String(component.opacity);
        element.style.zIndex = String(component.zIndex);
    }

    function componentTransformHandlesHtml(component) {
        if (!component || component.locked || Number(component.id) !== Number(selectedComponentId)) return '';
        return `
            <span class="component-transform-handles" aria-hidden="true">
                <button type="button" class="component-resize-handle is-nw" data-component-resize="nw" title="Redimensionar"></button>
                <button type="button" class="component-resize-handle is-ne" data-component-resize="ne" title="Redimensionar"></button>
                <button type="button" class="component-resize-handle is-sw" data-component-resize="sw" title="Redimensionar"></button>
                <button type="button" class="component-resize-handle is-se" data-component-resize="se" title="Redimensionar"></button>
            </span>
        `;
    }

    function resizeComponentByHandle(component, start, deltaX, deltaY, handle) {
        if (!component || !start || !handle) return;
        const horizontal = handle.includes('e') ? 1 : handle.includes('w') ? -1 : 0;
        const vertical = handle.includes('s') ? 1 : handle.includes('n') ? -1 : 0;
        let nextWidth = start.width + (deltaX * horizontal);
        let nextHeight = start.height + (deltaY * vertical);
        nextWidth = clamp(Math.round(nextWidth * 10) / 10, 4, 140);
        nextHeight = clamp(Math.round(nextHeight * 10) / 10, 2, 140);

        let nextX = start.x;
        let nextY = start.y;
        if (horizontal) nextX = start.x + (deltaX / 2);
        if (vertical) nextY = start.y + (deltaY / 2);

        component.x = Math.round(clamp(nextX, layerBounds.min, layerBounds.max) * 10) / 10;
        component.y = Math.round(clamp(nextY, layerBounds.min, layerBounds.max) * 10) / 10;
        component.width = nextWidth;
        component.height = nextHeight;
    }

    function applyRealContentStyles(element, cfg, sectionType = '') {
        const real = normalizeRealContentConfig(cfg.realContent, sectionType);
        element.classList.add('real-content-layer');
        element.dataset.realContentLayout = real.layout;
        element.dataset.realContentAlign = real.align;
        element.dataset.realContentShadow = real.cardShadow ? '1' : '0';
        element.dataset.realContentShowMedia = real.showMedia ? '1' : '0';
        element.dataset.realContentShowAddress = real.showAddress ? '1' : '0';
        element.dataset.realContentShowMaps = real.showMaps ? '1' : '0';
        element.style.setProperty('--real-content-offset-x', `${real.x - 50}%`);
        element.style.setProperty('--real-content-offset-y', `${real.y - 50}%`);
        element.style.setProperty('--real-content-width', `${real.width}%`);
        element.style.setProperty('--real-content-scale', real.scale);
        element.style.setProperty('--real-content-rotation', `${real.rotation}deg`);
        element.style.setProperty('--real-content-opacity', real.opacity);
        element.style.setProperty('--real-content-z', real.zIndex);
        element.style.setProperty('--real-content-gap', `${real.gap}px`);
        element.style.setProperty('--real-card-bg', real.cardBg);
        element.style.setProperty('--real-card-radius', `${real.cardRadius}px`);
        element.style.setProperty('--real-card-padding', `${real.cardPadding}px`);
        element.style.setProperty('--real-card-text-size', `${real.textSize}px`);
    }

    function builderComponentById(componentId) {
        const id = Number(componentId);
        return builderComponents.find((component) => Number(component.id) === id) || null;
    }

    function setRealComponentStyles(element, component) {
        if (!element || !component) return;
        element.style.setProperty('--component-x', `${component.x}%`);
        element.style.setProperty('--component-y', `${component.y}%`);
        element.style.setProperty('--component-width', `${component.width}%`);
        element.style.setProperty('--component-height', `${component.height}%`);
        element.style.setProperty('--component-rotation', `${component.rotation}deg`);
        element.style.setProperty('--component-opacity', component.opacity);
        element.style.setProperty('--component-z', component.zIndex);
    }

    function activeRealPreviewDocument() {
        try {
            return realPreviewFrame?.contentDocument || null;
        } catch (error) {
            return null;
        }
    }

    function emitRealPreviewComponentUpdate(component) {
        const frame = realPreviewFrame;
        if (!frame || !component) return;
        const message = {
            source: 'invitation-live-editor',
            type: 'component:update',
            component: componentPayload(component),
            componentId: component.id,
        };
        try {
            frame.contentWindow?.postMessage(message, window.location.origin);
            frame.contentDocument?.dispatchEvent(new CustomEvent('invitation-editor:component-updated', { detail: message }));
        } catch (error) {
            // Same-origin direct sync is best effort; saving to the API remains authoritative.
        }
    }

    function syncRealPreviewComponent(component) {
        const doc = activeRealPreviewDocument();
        if (!doc || !component) return;
        const element = doc.querySelector(`[data-component-id="${component.id}"]`);
        if (element) setRealComponentStyles(element, component);
        emitRealPreviewComponentUpdate(component);
        paintRealPreviewSelection(doc);
    }

    function selectedComponent() {
        return selectedComponentId ? builderComponentById(selectedComponentId) : null;
    }

    function updateComponentPreview(component) {
        if (!component) return;
        root.querySelectorAll(`[data-component-id="${component.id}"]`).forEach((element) => {
            element.classList.toggle('is-selected-component', selectedComponentId === component.id);
            element.classList.toggle('is-locked', component.locked);
            element.innerHTML = componentInnerHtml(component);
            setBuilderComponentStyles(element, component);
        });
        syncRealPreviewComponent(component);
    }

    function fillComponentProperties() {
        const panel = root.querySelector('[data-component-properties]');
        if (!panel) return;
        const component = selectedComponent();
        panel.hidden = !component;
        if (!component) return;

        const props = component.properties || {};
        const summary = panel.querySelector('[data-component-summary]');
        if (summary) {
            summary.textContent = `${component.tipo} #${component.id} - ${component.sectionType || 'seccion'}`;
        }

        panel.querySelectorAll('[data-component-field]').forEach((field) => {
            const key = field.dataset.componentField;
            if (field.type === 'checkbox') {
                field.checked = Boolean(component[key]);
            } else {
                field.value = component[key] ?? '';
            }
        });

        panel.querySelectorAll('[data-component-type-panel]').forEach((typePanel) => {
            typePanel.hidden = typePanel.dataset.componentTypePanel !== component.tipo;
        });

        panel.querySelectorAll('[data-component-property]').forEach((field) => {
            const key = field.dataset.componentProperty;
            if (field.type === 'color') {
                field.value = props[key] || '#263126';
            } else {
                field.value = props[key] ?? '';
            }
        });
    }

    function updateAssetDetailButtons() {
        const section = selectedSection();
        const detailsSelected = section && section.type === 'DETALLES';
        root.querySelectorAll('[data-asset-details-only]').forEach((element) => {
            element.hidden = !detailsSelected;
        });
        root.querySelectorAll('[data-asset-target]').forEach((select) => {
            select.querySelectorAll('option').forEach((option) => {
                if (['CEREMONIA', 'RECEPCION', 'MAPA_CEREMONIA', 'MAPA_RECEPCION'].includes(option.value)) {
                    option.disabled = !detailsSelected;
                }
            });
        });
    }

    function inspectorTargetType() {
        if (selectedComponent()) return 'component';
        const selector = root.querySelector('[data-inspector-target]');
        const requested = selector?.value || 'section';
        const section = selectedSection();
        if (!section) return 'none';
        if (requested === 'real' && realContentSections.has(section.type)) return 'real';
        if (requested === 'layer') return 'layer';
        return 'section';
    }

    function activeLayerConfig(section) {
        const cfg = ensureSectionConfig(section);
        const layer = cfg.activeLayer || 'background';
        if (isCustomLayer(layer)) {
            const custom = selectedCustomLayer(cfg);
            return custom ? { type: 'custom', layer, custom, cfg } : null;
        }
        return { type: layer, layer, cfg };
    }

    function getInspectorValue(target, field) {
        const section = selectedSection();
        if (!section || target === 'none') return '';
        const cfg = ensureSectionConfig(section);
        const component = selectedComponent();

        if (target === 'component' && component) {
            const map = { z: 'zIndex' };
            const key = map[field] || field;
            return component[key] ?? '';
        }

        if (target === 'real') {
            const real = normalizeRealContentConfig(cfg.realContent, section.type);
            const map = {
                height: 'scale',
                z: 'zIndex',
                locked: null,
                hidden: null,
            };
            const key = map[field] || field;
            if (!key) return false;
            return real[key] ?? '';
        }

        if (target === 'layer') {
            const layerState = activeLayerConfig(section);
            if (!layerState) return '';
            if (layerState.type === 'custom') {
                const map = { height: 'scale', z: 'z', rotation: 'rotation', opacity: 'opacity', hidden: 'visible' };
                const key = map[field] || field;
                if (field === 'hidden') return layerState.custom.visible === false;
                return layerState.custom[key] ?? '';
            }
            if (layerState.type === 'background') {
                const map = {
                    x: 'backgroundX',
                    y: 'backgroundY',
                    height: 'backgroundScale',
                    opacity: 'backgroundOpacity',
                    hidden: 'showBackgroundLayer',
                };
                if (field === 'width' || field === 'rotation' || field === 'z' || field === 'locked') return '';
                if (field === 'hidden') return cfg.showBackgroundLayer === false;
                const key = map[field];
                return key ? (effectiveBackgroundValue(cfg, key) ?? cfg[key] ?? '') : '';
            }
            const prefix = layerState.type;
            const keyMap = {
                x: `${prefix}X`,
                y: `${prefix}Y`,
                width: `${prefix}Width`,
                height: `${prefix}Scale`,
                rotation: `${prefix}Rotation`,
                opacity: `${prefix}Opacity`,
                z: `${prefix}Z`,
                locked: `${prefix}Locked`,
                hidden: `${prefix}Visible`,
            };
            if (field === 'hidden') return cfg[keyMap.hidden] === false;
            return cfg[keyMap[field]] ?? '';
        }

        if (target === 'section') {
            const values = {
                x: '',
                y: '',
                width: cfg.layoutWidth ?? 100,
                height: cfg.sectionHeight ?? 420,
                rotation: '',
                opacity: cfg.backgroundOpacity ?? 1,
                z: '',
                locked: '',
                hidden: section.visible === false,
            };
            return values[field] ?? '';
        }
        return '';
    }

    function setInspectorValue(target, field, rawValue) {
        const section = selectedSection();
        if (!section || target === 'none') return;
        const cfg = ensureSectionConfig(section);
        const component = selectedComponent();
        const isCheckbox = typeof rawValue === 'boolean';
        const value = isCheckbox ? rawValue : Number(rawValue);

        if (target === 'component' && component) {
            const map = { z: 'zIndex' };
            const key = map[field] || field;
            component[key] = isCheckbox ? rawValue : (Number.isFinite(value) ? value : rawValue);
            updateComponentPreview(component);
            return;
        }

        if (target === 'real') {
            const real = normalizeRealContentConfig(cfg.realContent, section.type);
            if (field === 'height') real.scale = Number.isFinite(value) ? value : real.scale;
            else if (field === 'z') real.zIndex = Number.isFinite(value) ? value : real.zIndex;
            else if (!['locked', 'hidden'].includes(field)) real[field] = Number.isFinite(value) ? value : rawValue;
            cfg.realContent = normalizeRealContentConfig(real, section.type);
            return;
        }

        if (target === 'layer') {
            const layerState = activeLayerConfig(section);
            if (!layerState) return;
            if (layerState.type === 'custom') {
                const keyMap = { height: 'scale', z: 'z' };
                if (field === 'hidden') layerState.custom.visible = !rawValue;
                else layerState.custom[keyMap[field] || field] = Number.isFinite(value) ? value : rawValue;
                return;
            }
            if (layerState.type === 'background') {
                if (field === 'hidden') cfg.showBackgroundLayer = !rawValue;
                else if (field === 'x') setBackgroundValue(cfg, 'backgroundX', value);
                else if (field === 'y') setBackgroundValue(cfg, 'backgroundY', value);
                else if (field === 'height') setBackgroundValue(cfg, 'backgroundScale', value);
                else if (field === 'opacity') cfg.backgroundOpacity = String(rawValue);
                return;
            }
            const prefix = layerState.type;
            const keyMap = {
                x: `${prefix}X`,
                y: `${prefix}Y`,
                width: `${prefix}Width`,
                height: `${prefix}Scale`,
                rotation: `${prefix}Rotation`,
                opacity: `${prefix}Opacity`,
                z: `${prefix}Z`,
                locked: `${prefix}Locked`,
                hidden: `${prefix}Visible`,
            };
            if (field === 'hidden') cfg[keyMap.hidden] = !rawValue;
            else cfg[keyMap[field]] = Number.isFinite(value) ? value : rawValue;
            return;
        }

        if (target === 'section') {
            if (field === 'width') cfg.layoutWidth = Number.isFinite(value) ? value : cfg.layoutWidth;
            else if (field === 'height') cfg.sectionHeight = Number.isFinite(value) ? value : cfg.sectionHeight;
            else if (field === 'opacity') cfg.backgroundOpacity = String(rawValue);
            else if (field === 'hidden') section.visible = !rawValue;
        }
    }

    function updateUniversalInspector() {
        const panel = root.querySelector('[data-universal-inspector]');
        if (!panel) return;
        const section = selectedSection();
        const component = selectedComponent();
        const target = inspectorTargetType();
        const kind = panel.querySelector('[data-inspector-kind]');
        const summary = panel.querySelector('[data-inspector-summary]');
        const selector = panel.querySelector('[data-inspector-target]');

        panel.classList.toggle('is-empty', !section && !component);
        if (selector) {
            selector.querySelector('option[value="component"]').disabled = !component;
            selector.querySelector('option[value="real"]').disabled = !section || !realContentSections.has(section.type);
            if (component && selector.value !== 'component') selector.value = 'component';
            if (!component && selector.value === 'component') selector.value = realContentSections.has(section?.type) ? 'real' : 'section';
        }

        const labels = {
            none: 'Sin seleccion',
            section: 'Seccion',
            layer: 'Capa',
            real: 'Contenido real',
            component: component ? component.tipo : 'Componente',
        };
        if (kind) kind.textContent = labels[target] || 'Inspector';
        if (summary) {
            if (target === 'component' && component) summary.textContent = `${component.tipo} en ${component.sectionType || 'seccion'} #${component.id}`;
            else if (section) summary.textContent = `${section.title || section.type} - ${labels[target] || target}`;
            else summary.textContent = 'Selecciona una seccion o componente.';
        }

        panel.querySelector('[data-inspector-action="delete-component"]')?.toggleAttribute('hidden', target !== 'component');
        panel.querySelectorAll('[data-inspector-field]').forEach((field) => {
            const key = field.dataset.inspectorField;
            const value = getInspectorValue(target, key);
            field.disabled = target === 'none' || value === '';
            if (field.type === 'checkbox') field.checked = Boolean(value);
            else if (value !== '') field.value = value;
        });
    }

    function fillRealContentProperties() {
        const panel = root.querySelector('[data-real-content-properties]');
        if (!panel) return;
        const section = selectedSection();
        const supported = section && realContentSections.has(section.type);
        panel.hidden = !supported;
        if (!supported) return;

        const real = ensureSectionConfig(section).realContent;
        const summary = panel.querySelector('[data-real-content-summary]');
        if (summary) {
            summary.textContent = section.type === 'DETALLES'
                ? 'Ceremonia y recepcion separadas, vinculadas a datos reales.'
                : `Acomodo visual del contenido dinamico de ${section.title || section.type}.`;
        }

        panel.querySelectorAll('[data-real-content-details-only]').forEach((element) => {
            element.hidden = section.type !== 'DETALLES';
        });
        panel.querySelectorAll('[data-real-content-generic-only]').forEach((element) => {
            element.hidden = section.type === 'DETALLES';
        });

        panel.querySelectorAll('[data-real-content-field]').forEach((field) => {
            const key = field.dataset.realContentField;
            if (field.type === 'checkbox') {
                field.checked = Boolean(real[key]);
            } else if (field.type === 'color') {
                field.value = real[key] || '#ffffff';
            } else {
                field.value = real[key] ?? '';
            }
        });

        panel.querySelectorAll('[data-real-content-items]').forEach((group) => {
            group.hidden = group.dataset.realContentItems !== section.type;
        });

        panel.querySelectorAll('[data-real-content-item]').forEach((field) => {
            const itemKey = field.dataset.realContentItem;
            const itemField = field.dataset.realContentItemField;
            const item = real.items?.[itemKey] || {};
            if (field.type === 'checkbox') {
                field.checked = item[itemField] !== false;
            } else if (field.type === 'color') {
                field.value = item[itemField] || '#ffffff';
            } else {
                field.value = item[itemField] ?? '';
            }
        });
    }

    function selectBuilderComponent(componentId, options = {}) {
        const component = builderComponentById(componentId);
        if (!component) return null;
        selectedComponentId = component.id;
        selectedId = component.sectionId;
        if (!options.skipRender) renderAll();
        paintRealPreviewSelection();
        if (!options.silent) setState(`Componente ${component.tipo.toLowerCase()} seleccionado`);
        return component;
    }

    function attachBuilderComponentDrag(article, element, component) {
        let dragging = null;
        element.addEventListener('click', (event) => {
            event.stopPropagation();
            selectedId = component.sectionId;
            selectedComponentId = component.id;
            renderAll();
        });
        element.addEventListener('pointerdown', (event) => {
            if (event.target.closest('[data-component-resize]')) return;
            if (component.locked) return;
            event.stopPropagation();
            selectedId = component.sectionId;
            selectedComponentId = component.id;
            const rect = article.getBoundingClientRect();
            dragging = {
                x: event.clientX,
                y: event.clientY,
                startX: component.x,
                startY: component.y,
                width: Math.max(rect.width, 1),
                height: Math.max(rect.height, 1),
            };
            element.setPointerCapture(event.pointerId);
        });
        element.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            const deltaX = ((event.clientX - dragging.x) / dragging.width) * 100;
            const deltaY = ((event.clientY - dragging.y) / dragging.height) * 100;
            component.x = Math.round(clamp(dragging.startX + deltaX, layerBounds.min, layerBounds.max));
            component.y = Math.round(clamp(dragging.startY + deltaY, layerBounds.min, layerBounds.max));
            setBuilderComponentStyles(element, component);
            setState('Moviendo componente...');
        });
        element.addEventListener('pointerup', () => {
            if (!dragging) return;
            dragging = null;
            saveBuilderComponent(component, { skipRealRefresh: true }).catch((error) => setState(error.message));
        });
        element.addEventListener('pointercancel', () => { dragging = null; });
    }

    function attachBuilderComponentResize(article, element, component) {
        let resizing = null;
        element.querySelectorAll('[data-component-resize]').forEach((handle) => {
            handle.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
            });
            handle.addEventListener('pointerdown', (event) => {
                if (component.locked) return;
                event.preventDefault();
                event.stopPropagation();
                selectedId = component.sectionId;
                selectedComponentId = component.id;
                const rect = article.getBoundingClientRect();
                resizing = {
                    handle: handle.dataset.componentResize,
                    x: event.clientX,
                    y: event.clientY,
                    start: {
                        x: component.x,
                        y: component.y,
                        width: component.width,
                        height: component.height,
                    },
                    width: Math.max(rect.width, 1),
                    height: Math.max(rect.height, 1),
                };
                handle.setPointerCapture(event.pointerId);
                setState('Redimensionando componente...');
            });
            handle.addEventListener('pointermove', (event) => {
                if (!resizing) return;
                event.preventDefault();
                event.stopPropagation();
                const deltaX = ((event.clientX - resizing.x) / resizing.width) * 100;
                const deltaY = ((event.clientY - resizing.y) / resizing.height) * 100;
                resizeComponentByHandle(component, resizing.start, deltaX, deltaY, resizing.handle);
                setBuilderComponentStyles(element, component);
                fillProperties();
            });
            handle.addEventListener('pointerup', (event) => {
                if (!resizing) return;
                event.preventDefault();
                event.stopPropagation();
                resizing = null;
                saveBuilderComponent(component, { skipRealRefresh: true }).catch((error) => setState(error.message));
            });
            handle.addEventListener('pointercancel', () => { resizing = null; });
        });
    }

    function renderBuilderComponents(article, section) {
        componentsForSection(section).forEach((component) => {
            const element = document.createElement('div');
            element.className = 'preview-builder-component';
            element.dataset.componentId = String(component.id);
            element.dataset.componentType = component.tipo;
            element.classList.toggle('is-selected-component', selectedComponentId === component.id);
            element.classList.toggle('is-locked', component.locked);
            element.innerHTML = componentInnerHtml(component) + componentTransformHandlesHtml(component);
            setBuilderComponentStyles(element, component);
            attachBuilderComponentDrag(article, element, component);
            attachBuilderComponentResize(article, element, component);
            article.appendChild(element);
        });
    }

    function refreshRealPreview() {
        const frame = realPreviewFrame;
        if (!frame) return;
        const url = new URL(frame.src, window.location.href);
        url.searchParams.set('_editor_ts', Date.now().toString());
        frame.src = url.toString();
    }

    function clamp(value, min, max) {
        const number = Number(value);
        if (Number.isNaN(number)) return min;
        return Math.min(Math.max(number, min), max);
    }

    function backgroundSizeValue(cfg) {
        const scale = clamp(effectiveBackgroundValue(cfg, 'backgroundScale') ?? 1, 0.4, 3);
        if (cfg.backgroundFit === 'cover') return `auto ${Math.round(scale * 100)}%`;
        if (cfg.backgroundFit === 'repeat') return `${Math.max(Math.round(scale * 140), 40)}px auto`;
        if (cfg.backgroundFit === 'free') return `${Math.max(Math.round(scale * 100), 40)}% auto`;
        return 'contain';
    }

    function backgroundRepeatValue(cfg) {
        return cfg.backgroundFit === 'repeat' || cfg.backgroundRepeat === 'repeat' ? 'repeat' : 'no-repeat';
    }

    function setBackgroundStyles(layer, cfg, asset) {
        layer.style.opacity = String(clamp(cfg.backgroundOpacity ?? 1, 0, 1));
        layer.style.backgroundSize = backgroundSizeValue(cfg);
        layer.style.backgroundRepeat = backgroundRepeatValue(cfg);
        layer.style.backgroundPosition = `${clamp(effectiveBackgroundValue(cfg, 'backgroundX') ?? 50, 0, 100)}% ${clamp(effectiveBackgroundValue(cfg, 'backgroundY') ?? 50, 0, 100)}%`;
        layer.style.filter = `brightness(${clamp(cfg.backgroundBrightness ?? 1, 0.35, 1.75)}) blur(${clamp(cfg.backgroundBlur ?? 0, 0, 12)}px)`;
        if (asset?.url && !asset.isVideo) {
            layer.style.backgroundImage = `url("${asset.url}")`;
        }
    }

    function deviceSuffix() {
        if (currentDeviceMode === 'desktop') return 'Desktop';
        if (currentDeviceMode === 'tablet') return 'Tablet';
        return 'Mobile';
    }

    function deviceScopedBackgroundKey(key) {
        if (!['backgroundX', 'backgroundY', 'backgroundScale'].includes(key)) return key;
        return `${key}${deviceSuffix()}`;
    }

    function effectiveBackgroundValue(cfg, key) {
        const scoped = deviceScopedBackgroundKey(key);
        return cfg[scoped] ?? cfg[key];
    }

    function setBackgroundValue(cfg, key, value) {
        cfg[deviceScopedBackgroundKey(key)] = value;
    }

    function thumbnailBackgroundStyle(cfg, asset) {
        const style = [];
        if (asset?.url && !asset.isVideo) style.push(`background-image:url("${asset.url}")`);
        style.push(`background-size:${backgroundSizeValue(cfg)}`);
        style.push(`background-position:${clamp(effectiveBackgroundValue(cfg, 'backgroundX') ?? 50, 0, 100)}% ${clamp(effectiveBackgroundValue(cfg, 'backgroundY') ?? 50, 0, 100)}%`);
        return style.join(';');
    }

    function sectionThumbnailHtml(section, cfg, background) {
        const customCount = ensureCustomLayers(cfg).length;
        const dataText = sectionPreviewHtml(section).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 82);
        return `
            <button type="button" class="section-thumb-card" data-section-thumb style="${thumbnailBackgroundStyle(cfg, background)}">
                ${background?.isVideo ? '<span class="section-thumb-video">Video</span>' : ''}
                <span class="section-thumb-title">${escapeHtml(section.title || section.type)}</span>
                <span class="section-thumb-copy">${escapeHtml(dataText || section.type.replaceAll('_', ' '))}</span>
                <span class="section-thumb-meta">${customCount} capa(s)</span>
            </button>
        `;
    }

    function layerPrefix(layer) {
        return {
            title: 'title',
            text: 'text',
            decor: 'decor',
        }[layer] || 'title';
    }

    function layerDefaults(layer) {
        if (layer === 'decor') return { x: 50, y: 12, scale: 1, opacity: 0.42, visible: false, rotation: 0, locked: false, z: 1, width: 36, align: 'center' };
        if (layer === 'text') return { x: 50, y: 50, scale: 1, opacity: 1, visible: true, rotation: 0, locked: false, z: 2, width: 78, align: 'center' };
        return { x: 50, y: 50, scale: 1, opacity: 1, visible: true, rotation: 0, locked: false, z: 2, width: 72, align: 'center' };
    }

    function layerValue(cfg, layer, field) {
        const prefix = layerPrefix(layer);
        const defaults = layerDefaults(layer);
        const key = layer === 'text' && field === 'align' ? 'textAlignLayer' : `${prefix}${field[0].toUpperCase()}${field.slice(1)}`;
        return cfg[key] ?? defaults[field];
    }

    function setLayerValue(cfg, layer, field, value) {
        const prefix = layerPrefix(layer);
        const key = layer === 'text' && field === 'align' ? 'textAlignLayer' : `${prefix}${field[0].toUpperCase()}${field.slice(1)}`;
        cfg[key] = value;
    }

    function setLayerStyles(element, cfg, layer) {
        const x = clamp(layerValue(cfg, layer, 'x'), layerBounds.min, layerBounds.max);
        const y = clamp(layerValue(cfg, layer, 'y'), layerBounds.min, layerBounds.max);
        const scale = clamp(layerValue(cfg, layer, 'scale'), 0.5, 2.2);
        const rotation = clamp(layerValue(cfg, layer, 'rotation'), -45, 45);
        const opacity = clamp(layerValue(cfg, layer, 'opacity'), 0, 1);
        const z = clamp(layerValue(cfg, layer, 'z'), 1, 5);
        const width = clamp(layerValue(cfg, layer, 'width'), 12, 100);
        const align = ['left', 'center', 'right'].includes(layerValue(cfg, layer, 'align')) ? layerValue(cfg, layer, 'align') : 'center';
        element.style.setProperty('--layer-x', `${x}%`);
        element.style.setProperty('--layer-y', `${y}%`);
        element.style.setProperty('--layer-scale', scale);
        element.style.setProperty('--layer-rotation', `${rotation}deg`);
        element.style.setProperty('--layer-width', `${width}%`);
        element.style.textAlign = align;
        element.style.opacity = String(opacity);
        element.style.zIndex = String(z);
        element.classList.toggle('is-hidden', layerValue(cfg, layer, 'visible') === false);
        element.classList.toggle('is-locked', layerValue(cfg, layer, 'locked') === true);
    }

    function decorText(style) {
        return {
            line: '-',
            flourish: '~',
            rings: 'oo',
            dots: '. . .',
        }[style] || '-';
    }

    function sectionAssetLabel(asset) {
        if (!asset?.url) return 'Sin fondo';
        return asset.isVideo ? 'Video' : 'Imagen';
    }

    function assetReferenceFromItem(item) {
        return {
            id: Number(item.dataset.assetId),
            url: item.dataset.assetUrl,
            title: item.dataset.assetTitle,
            isVideo: item.dataset.assetVideo === '1',
        };
    }

    function customLayerId() {
        if (window.crypto?.randomUUID) return `layer-${window.crypto.randomUUID()}`;
        return `layer-${Date.now()}-${Math.round(Math.random() * 100000)}`;
    }

    function normalizeCustomLayer(layer) {
        const isMedia = layer.kind === 'image' || layer.kind === 'video';
        return {
            id: layer.id || customLayerId(),
            kind: isMedia ? layer.kind : 'text',
            name: (layer.name || (isMedia ? 'Imagen libre' : 'Texto libre')).slice(0, 80),
            text: (layer.text || 'Texto editable').slice(0, 220),
            asset: layer.asset || {},
            x: clamp(layer.x ?? 50, layerBounds.min, layerBounds.max),
            y: clamp(layer.y ?? 50, layerBounds.min, layerBounds.max),
            scale: clamp(layer.scale ?? 1, 0.35, 3),
            opacity: clamp(layer.opacity ?? 1, 0, 1),
            rotation: clamp(layer.rotation ?? 0, -180, 180),
            z: clamp(layer.z ?? 3, 1, 12),
            width: clamp(layer.width ?? (isMedia ? 42 : 64), 8, 120),
            align: ['left', 'center', 'right'].includes(layer.align) ? layer.align : 'center',
            visible: layer.visible !== false,
            locked: layer.locked === true,
            fit: ['contain', 'cover'].includes(layer.fit) ? layer.fit : 'contain',
        };
    }

    function ensureCustomLayers(cfg) {
        const layers = Array.isArray(cfg.customLayers) ? cfg.customLayers : [];
        return layers.map(normalizeCustomLayer).slice(0, 60);
    }

    function isCustomLayer(layer) {
        return String(layer || '').startsWith('custom:');
    }

    function customLayerByActive(cfg) {
        if (!isCustomLayer(cfg.activeLayer)) return null;
        const id = String(cfg.activeLayer).replace('custom:', '');
        cfg.customLayers = ensureCustomLayers(cfg);
        return cfg.customLayers.find((layer) => layer.id === id) || null;
    }

    function customLayerValue(layer, field) {
        return normalizeCustomLayer(layer)[field];
    }

    function setCustomLayerValue(layer, field, value) {
        layer[field] = value;
    }

    function setCustomLayerStyles(element, layer) {
        const clean = normalizeCustomLayer(layer);
        element.style.setProperty('--layer-x', `${clean.x}%`);
        element.style.setProperty('--layer-y', `${clean.y}%`);
        element.style.setProperty('--layer-scale', clean.scale);
        element.style.setProperty('--layer-rotation', `${clean.rotation}deg`);
        element.style.setProperty('--layer-width', `${clean.width}%`);
        element.style.opacity = String(clean.opacity);
        element.style.textAlign = clean.align;
        element.style.zIndex = String(clean.z);
        element.classList.toggle('is-hidden', clean.visible === false);
        element.classList.toggle('is-locked', clean.locked === true);
    }

    function selectSectionByType(type, layer = null) {
        const section = sortedSections().find((item) => item.type === type);
        if (!section) return;
        selectedId = section.sectionId;
        if (layer) {
            const cfg = ensureSectionConfig(section);
            if (['background', 'title', 'text', 'decor'].includes(layer)) {
                cfg.activeLayer = layer;
            } else if (isCustomLayer(layer)) {
                cfg.customLayers = ensureCustomLayers(cfg);
                if (cfg.customLayers.some((item) => `custom:${item.id}` === layer)) {
                    cfg.activeLayer = layer;
                }
            }
        }
        renderAll();
    }

    function setLivePreviewMode(mode) {
        livePreviewMode = mode === 'test' ? 'test' : 'edit';
        root.dataset.livePreviewMode = livePreviewMode;
        root.querySelectorAll('[data-live-preview-mode]').forEach((button) => {
            button.classList.toggle('is-active', button.dataset.livePreviewMode === livePreviewMode);
        });
        const hint = root.querySelector('[data-live-preview-hint]');
        if (hint) {
            hint.textContent = livePreviewMode === 'test'
                ? 'Modo probar: botones, enlaces, mapas y formularios funcionan realmente'
                : 'Modo editar: selecciona y mueve componentes sobre la invitacion real';
        }
        applyRealPreviewMode();
    }

    function ensureRealPreviewStyle(doc) {
        if (!doc || doc.getElementById('editor-real-preview-style')) return;
        const style = doc.createElement('style');
        style.id = 'editor-real-preview-style';
        style.textContent = `
            html[data-editor-live-mode="edit"] [data-invitation-section] { position: relative; cursor: crosshair; }
            html[data-editor-live-mode="edit"] iframe,
            html[data-editor-live-mode="edit"] embed,
            html[data-editor-live-mode="edit"] object { pointer-events: none !important; }
            html[data-editor-live-mode="edit"] .invitation-component { cursor: grab; touch-action: none; }
            html[data-editor-live-mode="edit"] .invitation-component:active { cursor: grabbing; }
            .editor-real-selected {
                outline: 2px solid rgba(199, 125, 146, .76) !important;
                outline-offset: -4px !important;
            }
            .editor-real-layer {
                outline: 2px dashed rgba(38, 49, 38, .72) !important;
                outline-offset: 5px !important;
            }
            .editor-real-component-selected {
                outline: 2px solid #2563eb !important;
                outline-offset: 4px !important;
                box-shadow: 0 0 0 7px rgba(37, 99, 235, .12) !important;
            }
            .editor-live-selection-label {
                position: absolute;
                left: 50%;
                top: -26px;
                z-index: 9999;
                transform: translateX(-50%);
                border-radius: 999px;
                background: #2563eb;
                color: #fff;
                font-family: Inter, Arial, sans-serif;
                font-size: 11px;
                font-weight: 800;
                line-height: 1;
                padding: 6px 8px;
                pointer-events: none;
                white-space: nowrap;
            }
            .editor-live-selection-handle {
                position: absolute;
                z-index: 9999;
                width: 13px;
                height: 13px;
                border: 2px solid #fff;
                border-radius: 50%;
                background: #2563eb;
                box-shadow: 0 1px 4px rgba(15, 23, 42, .28);
                cursor: nwse-resize;
                pointer-events: auto;
                touch-action: none;
            }
            .editor-live-selection-handle[data-handle="nw"] { left: -7px; top: -7px; }
            .editor-live-selection-handle[data-handle="ne"] { right: -7px; top: -7px; cursor: nesw-resize; }
            .editor-live-selection-handle[data-handle="sw"] { left: -7px; bottom: -7px; cursor: nesw-resize; }
            .editor-live-selection-handle[data-handle="se"] { right: -7px; bottom: -7px; }
            .editor-live-section-label {
                position: absolute;
                left: 12px;
                top: 12px;
                z-index: 9999;
                border-radius: 999px;
                background: rgba(38, 49, 38, .88);
                color: #fff;
                font-family: Inter, Arial, sans-serif;
                font-size: 11px;
                font-weight: 800;
                padding: 6px 9px;
                pointer-events: none;
            }
            .custom-public-layer { pointer-events: auto !important; }
        `;
        doc.head.appendChild(style);
    }

    function clearRealPreviewSelection(doc) {
        if (!doc) return;
        doc.querySelectorAll('.editor-real-selected').forEach((item) => item.classList.remove('editor-real-selected'));
        doc.querySelectorAll('.editor-real-layer').forEach((item) => item.classList.remove('editor-real-layer'));
        doc.querySelectorAll('.editor-real-component-selected').forEach((item) => item.classList.remove('editor-real-component-selected'));
        doc.querySelectorAll('.editor-live-selection-label, .editor-live-selection-handle, .editor-live-section-label').forEach((item) => item.remove());
    }

    function paintRealPreviewSelection(doc = activeRealPreviewDocument()) {
        if (!doc) return;
        clearRealPreviewSelection(doc);
        const component = selectedComponent();
        if (component) {
            const componentEl = doc.querySelector(`[data-component-id="${component.id}"]`);
            if (componentEl) {
                componentEl.classList.add('editor-real-component-selected');
                const label = doc.createElement('span');
                label.className = 'editor-live-selection-label';
                label.textContent = `${component.tipo} #${component.id}`;
                componentEl.appendChild(label);
                ['nw', 'ne', 'sw', 'se'].forEach((handleName) => {
                    const handle = doc.createElement('span');
                    handle.className = 'editor-live-selection-handle';
                    handle.dataset.handle = handleName;
                    componentEl.appendChild(handle);
                });
                return;
            }
        }
        const section = selectedSection();
        if (!section) return;
        const sectionEl = doc.querySelector(`[data-invitation-section="${section.type}"]`);
        if (!sectionEl) return;
        sectionEl.classList.add('editor-real-selected');
        const label = doc.createElement('span');
        label.className = 'editor-live-section-label';
        label.textContent = section.type.replaceAll('_', ' ');
        sectionEl.appendChild(label);
    }

    function applyRealPreviewMode(doc = activeRealPreviewDocument()) {
        if (!doc) return;
        ensureRealPreviewStyle(doc);
        doc.documentElement.dataset.editorLiveMode = livePreviewMode;
        if (livePreviewMode === 'edit') paintRealPreviewSelection(doc);
        else clearRealPreviewSelection(doc);
    }

    function layerFromRealPreviewTarget(target) {
        const custom = target.closest('.custom-public-layer[data-editor-layer]');
        if (custom) return { layer: custom.dataset.editorLayer, element: custom };
        const title = target.closest('.section-title, .section-title-image, .section-full-image, .cover-names, .cover-topline, .cover-date');
        if (title) return { layer: 'title', element: title };
        const text = target.closest('.section-copy, .event-detail-grid, .count-grid, .dress-visual, .menu-grid, .gift-grid, .album-grid, .form-grid, .guest-box, .cover-honors, .itinerary-list, .section-main-content, .invitation-summary');
        if (text) return { layer: 'text', element: text };
        return { layer: 'background', element: null };
    }

    function startRealComponentDrag(event, componentEl, component) {
        if (!component || component.locked) return;
        const stage = componentEl.parentElement;
        const rect = stage?.getBoundingClientRect();
        if (!rect || rect.width <= 0 || rect.height <= 0) return;
        realPreviewDrag = {
            mode: 'move',
            pointerId: event.pointerId,
            component,
            componentEl,
            startClientX: event.clientX,
            startClientY: event.clientY,
            startX: component.x,
            startY: component.y,
            width: rect.width,
            height: rect.height,
        };
        componentEl.setPointerCapture?.(event.pointerId);
        setState('Moviendo componente sobre vista real...');
    }

    function startRealComponentResize(event, handleEl, componentEl, component) {
        if (!component || component.locked) return;
        const stage = componentEl.parentElement;
        const rect = stage?.getBoundingClientRect();
        if (!rect || rect.width <= 0 || rect.height <= 0) return;
        realPreviewDrag = {
            mode: 'resize',
            pointerId: event.pointerId,
            component,
            componentEl,
            handle: handleEl.dataset.handle,
            startClientX: event.clientX,
            startClientY: event.clientY,
            start: {
                x: component.x,
                y: component.y,
                width: component.width,
                height: component.height,
            },
            width: rect.width,
            height: rect.height,
        };
        handleEl.setPointerCapture?.(event.pointerId);
        setState('Redimensionando componente sobre vista real...');
    }

    function updateRealComponentDrag(event) {
        if (!realPreviewDrag) return;
        const drag = realPreviewDrag;
        const deltaX = ((event.clientX - drag.startClientX) / drag.width) * 100;
        const deltaY = ((event.clientY - drag.startClientY) / drag.height) * 100;
        if (drag.mode === 'resize') {
            resizeComponentByHandle(drag.component, drag.start, deltaX, deltaY, drag.handle);
        } else {
            drag.component.x = Math.round(clamp(drag.startX + deltaX, layerBounds.min, layerBounds.max) * 10) / 10;
            drag.component.y = Math.round(clamp(drag.startY + deltaY, layerBounds.min, layerBounds.max) * 10) / 10;
        }
        setRealComponentStyles(drag.componentEl, drag.component);
        emitRealPreviewComponentUpdate(drag.component);
    }

    function finishRealComponentDrag() {
        if (!realPreviewDrag) return;
        const component = realPreviewDrag.component;
        realPreviewDrag = null;
        renderAll();
        saveBuilderComponent(component, { skipRealRefresh: true }).catch((error) => setState(error.message));
    }


    function normalizeNativeElement(node) {
        return {
            id: node.dataset.elementId || '',
            type: node.dataset.elementType || 'unknown',
            role: node.dataset.elementRole || '',
            section: node.dataset.elementSection || '',
            item: node.dataset.elementItem || '',
            node,
        };
    }

    function registerNativeElements(frameDocument) {
        if (!frameDocument) {
            nativeElementRegistry = [];
            return nativeElementRegistry;
        }

        const seen = new Set();
        nativeElementRegistry = [...frameDocument.querySelectorAll('[data-native-element]')]
            .map(normalizeNativeElement)
            .filter((element) => {
                if (!element.id || seen.has(element.id)) return false;
                seen.add(element.id);
                return true;
            });

        root.dataset.nativeElementCount = String(nativeElementRegistry.length);
        console.info(`DIRTEC Element Registry: ${nativeElementRegistry.length} elementos nativos registrados.`);
        return nativeElementRegistry;
    }

    function nativeElementById(elementId) {
        return nativeElementRegistry.find((element) => element.id === elementId) || null;
    }

    function bindRealPreviewInteractions() {
        const frame = realPreviewFrame;
        if (!frame) return;
        try {
            const doc = frame.contentDocument;
            if (!doc) return;

            /*
             * S03-P01
             * Registrar siempre antes de comprobar si los listeners
             * del iframe ya fueron conectados.
             */
            registerNativeElements(doc);

            ensureRealPreviewStyle(doc);
            applyRealPreviewMode(doc);

            if (doc.__invitationLiveEditorBound) return;
            doc.__invitationLiveEditorBound = true;

            doc.addEventListener('pointerdown', (event) => {
                if (livePreviewMode !== 'edit') return;
                const resizeHandle = event.target.closest('.editor-live-selection-handle[data-handle]');
                if (resizeHandle) {
                    const componentEl = resizeHandle.closest('[data-component-id]');
                    const component = selectBuilderComponent(componentEl?.dataset.componentId, { skipRender: true, silent: true });
                    if (!componentEl || !component) return;
                    event.preventDefault();
                    event.stopPropagation();
                    paintRealPreviewSelection(doc);
                    startRealComponentResize(event, resizeHandle, componentEl, component);
                    return;
                }
                const componentEl = event.target.closest('[data-component-id]');
                const sectionEl = event.target.closest('[data-invitation-section]');
                if (!componentEl && !sectionEl) return;
                event.preventDefault();
                event.stopPropagation();
                if (componentEl) {
                    const component = selectBuilderComponent(componentEl.dataset.componentId, { skipRender: true, silent: true });
                    paintRealPreviewSelection(doc);
                    startRealComponentDrag(event, componentEl, component);
                    return;
                }
                selectedComponentId = null;
                const selected = layerFromRealPreviewTarget(event.target);
                selectSectionByType(sectionEl.dataset.invitationSection, selected.layer);
                paintRealPreviewSelection(doc);
                setState(`Vista real: ${sectionEl.dataset.invitationSection.replaceAll('_', ' ')} / ${selected.layer.replace('custom:', 'capa ')}`);
            }, true);

            doc.addEventListener('pointermove', (event) => {
                if (livePreviewMode !== 'edit' || !realPreviewDrag) return;
                event.preventDefault();
                event.stopPropagation();
                updateRealComponentDrag(event);
            }, true);

            doc.addEventListener('pointerup', (event) => {
                if (livePreviewMode !== 'edit' || !realPreviewDrag) return;
                event.preventDefault();
                event.stopPropagation();
                finishRealComponentDrag();
            }, true);

            doc.addEventListener('pointercancel', () => { realPreviewDrag = null; }, true);

            doc.addEventListener('click', (event) => {
                if (livePreviewMode !== 'edit') return;
                if (event.target.closest('[data-invitation-section], [data-component-id], a, button, input, textarea, select, iframe')) {
                    event.preventDefault();
                    event.stopPropagation();
                }
            }, true);

            doc.addEventListener('submit', (event) => {
                if (livePreviewMode !== 'edit') return;
                event.preventDefault();
                event.stopPropagation();
            }, true);
        } catch (error) {
            setState('La vista real esta protegida por el navegador, usa el diseno rapido para editar.');
        }
    }

    function sortedSections() {
        return [...(config.sections || [])].sort((a, b) => {
            const byOrder = Number(a.order || 0) - Number(b.order || 0);
            return byOrder || Number(a.sectionId || 0) - Number(b.sectionId || 0);
        });
    }

    function selectedSection() {
        return (config.sections || []).find((section) => section.sectionId === selectedId) || null;
    }

    function applyTheme() {
        const theme = config.theme || {};
        const palette = paletteMap[theme.palette] || paletteMap.TINTA_MARFIL;
        const fonts = fontMap[theme.fontStyle] || fontMap.CURSIVA_ELEGANTE;
        root.style.setProperty('--editor-primary', theme.primary || palette[0]);
        root.style.setProperty('--editor-bg', theme.background || palette[1]);
        root.style.setProperty('--editor-accent', theme.accent || palette[2]);
        root.style.setProperty('--editor-soft', theme.secondary || palette[3]);
        root.style.setProperty('--editor-title-font', `'${fonts[0]}', cursive`);
        root.style.setProperty('--editor-body-font', `'${fonts[1]}', sans-serif`);
    }

    function renderSectionList() {
        sectionList.innerHTML = '';
        sortedSections().forEach((section, index) => {
            const cfg = ensureSectionConfig(section);
            const background = cfg.backgroundAsset || {};
            const item = document.createElement('article');
            item.className = 'section-item';
            item.draggable = true;
            item.dataset.sectionId = String(section.sectionId);
            item.classList.toggle('is-selected', section.sectionId === selectedId);
            item.classList.toggle('is-hidden', !section.visible);
            item.innerHTML = `
                <button type="button" class="section-main">
                    <strong>${escapeHtml(section.title || section.type)}</strong>
                    <span>${section.type.replaceAll('_', ' ')}</span>
                </button>
                <div class="section-controls">
                    <button type="button" data-move="-1" aria-label="Subir">↑</button>
                    <button type="button" data-move="1" aria-label="Bajar">↓</button>
                </div>
            `;
            const mainButton = item.querySelector('.section-main');
            const detail = mainButton.querySelector('span');
            detail.textContent = `${section.type.replaceAll('_', ' ')} - ${sectionAssetLabel(background)}`;
            const thumbWrap = document.createElement('div');
            thumbWrap.innerHTML = sectionThumbnailHtml(section, cfg, background);
            const thumb = thumbWrap.firstElementChild;
            item.insertBefore(thumb, mainButton);
            item.querySelector('.section-main').addEventListener('click', () => {
                selectedId = section.sectionId;
                renderAll();
            });
            thumb.addEventListener('click', () => {
                selectedId = section.sectionId;
                renderAll();
            });
            item.querySelectorAll('[data-move]').forEach((button) => {
                button.addEventListener('click', () => moveSection(index, Number(button.dataset.move)));
            });
            item.addEventListener('dragstart', (event) => {
                event.dataTransfer.setData('text/plain', String(section.sectionId));
                item.classList.add('is-dragging');
            });
            item.addEventListener('dragend', () => item.classList.remove('is-dragging'));
            item.addEventListener('dragover', (event) => event.preventDefault());
            item.addEventListener('drop', (event) => {
                event.preventDefault();
                reorderByDrop(Number(event.dataTransfer.getData('text/plain')), section.sectionId);
            });
            sectionList.appendChild(item);
        });
    }

    function componentTreeRow({
        level = 0,
        kind = '',
        label = '',
        meta = '',
        active = false,
        muted = false,
        action = '',
        sectionId = '',
        layerId = '',
        componentId = '',
        canHide = false,
        canLock = false,
        canMove = false,
        canDelete = false,
        locked = false,
        visible = true,
        canReorder = false,
    }) {
        const tools = [];
        if (canHide) {
            tools.push(`<button type="button" title="${visible ? 'Ocultar' : 'Mostrar'}" data-tree-tool="toggle-visible">${visible ? 'Ocultar' : 'Mostrar'}</button>`);
        }
        if (canLock) {
            tools.push(`<button type="button" title="${locked ? 'Desbloquear' : 'Bloquear'}" data-tree-tool="toggle-lock">${locked ? 'Abrir' : 'Bloquear'}</button>`);
        }
        if (canMove) {
            tools.push('<button type="button" title="Enviar atras" data-tree-tool="z-back">Atras</button>');
            tools.push('<button type="button" title="Traer al frente" data-tree-tool="z-front">Frente</button>');
        }
        if (canDelete) {
            tools.push('<button type="button" title="Eliminar" class="danger-link" data-tree-tool="delete">Eliminar</button>');
        }
        return `
            <article
                class="component-tree-row ${active ? 'is-active' : ''} ${muted ? 'is-muted' : ''}"
                style="--tree-level:${level};"
                draggable="${canReorder ? 'true' : 'false'}"
                data-tree-action="${escapeHtml(action)}"
                data-tree-section-id="${escapeHtml(sectionId)}"
                data-tree-layer-id="${escapeHtml(layerId)}"
                data-tree-component-id="${escapeHtml(componentId)}"
            >
                <button
                    type="button"
                    class="component-tree-main"
                    data-tree-action="${escapeHtml(action)}"
                    data-tree-section-id="${escapeHtml(sectionId)}"
                    data-tree-layer-id="${escapeHtml(layerId)}"
                    data-tree-component-id="${escapeHtml(componentId)}"
                >
                    <span class="tree-kind">${escapeHtml(kind)}</span>
                    <span class="tree-label">${escapeHtml(label)}</span>
                    ${meta ? `<small>${escapeHtml(meta)}</small>` : ''}
                </button>
                ${tools.length ? `<div class="component-tree-tools">${tools.join('')}</div>` : ''}
            </article>
        `;
    }

    function renderComponentTree() {
        if (!componentTree) return;
        const sections = sortedSections();
        const selected = selectedSection();
        const selectedCfg = selected ? ensureSectionConfig(selected) : {};
        const activeLayer = selectedCfg.activeLayer || '';
        const rows = [
            componentTreeRow({
                level: 0,
                kind: 'Pagina',
                label: 'Invitacion',
                meta: `${sections.length} secciones`,
                action: 'page',
                active: !selected,
            }),
        ];

        sections.forEach((section) => {
            const cfg = ensureSectionConfig(section);
            const sectionActive = Number(section.sectionId) === Number(selectedId) && !selectedComponentId;
            rows.push(componentTreeRow({
                level: 1,
                kind: 'Seccion',
                label: section.title || section.type,
                meta: section.type.replaceAll('_', ' '),
                action: 'section',
                sectionId: section.sectionId,
                active: sectionActive && !activeLayer,
                muted: section.visible === false,
                canHide: true,
                visible: section.visible !== false,
            }));

            layerListItems(cfg).forEach((layer) => {
                rows.push(componentTreeRow({
                    level: 2,
                    kind: layer.type,
                    label: layer.label,
                    meta: layer.locked ? 'Bloqueada' : `z ${layer.z || 0}`,
                    action: 'layer',
                    sectionId: section.sectionId,
                    layerId: layer.id,
                    active: Number(section.sectionId) === Number(selectedId) && !selectedComponentId && activeLayer === layer.id,
                    muted: layer.visible === false,
                    canHide: true,
                    canLock: layer.canLock,
                    canMove: layer.canMove,
                    canDelete: isCustomLayer(layer.id),
                    locked: layer.locked,
                    visible: layer.visible !== false,
                    canReorder: layer.canMove,
                }));
            });

            if (realContentSections.has(section.type)) {
                rows.push(componentTreeRow({
                    level: 2,
                    kind: 'Datos',
                    label: 'Contenido real',
                    meta: section.type === 'DETALLES' ? 'Ceremonia / Recepcion' : 'Dinamico',
                    action: 'real',
                    sectionId: section.sectionId,
                    active: Number(section.sectionId) === Number(selectedId) && root.querySelector('[data-inspector-target]')?.value === 'real',
                }));
            }

            builderComponents
                .filter((component) => Number(component.sectionId) === Number(section.sectionId))
                .sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0))
                .forEach((component) => {
                    rows.push(componentTreeRow({
                        level: 2,
                        kind: component.tipo,
                        label: component.properties?.label || component.properties?.text || component.properties?.alt || `Componente #${component.id}`,
                        meta: `z ${component.zIndex || 0}`,
                        action: 'component',
                        sectionId: section.sectionId,
                        componentId: component.id,
                        active: Number(component.id) === Number(selectedComponentId),
                        muted: component.hidden,
                        canHide: true,
                        canLock: true,
                        canMove: true,
                        canDelete: true,
                        locked: component.locked,
                        visible: component.hidden !== true,
                        canReorder: true,
                    }));
                });
        });

        componentTree.innerHTML = rows.join('');
    }


    function isFullImageSection(section, cfg) {
        const hasFullImage =
            Boolean(cfg.titleAsset?.url) ||
            Boolean(cfg.backgroundAsset?.url);

        return cfg.layoutMode === 'full-image' && hasFullImage;
    }

    function defaultKeepRealContent(sectionType) {
        return [
            'CUENTA_REGRESIVA',
            'DETALLES',
            'ALBUM',
            'REGALOS',
            'ALBUM_COMPARTIDO',
        ].includes(sectionType);
    }

    function sectionKeepsRealContent(section, cfg) {
        if (!isFullImageSection(section, cfg)) return true;
        if (typeof cfg.keepRealContent === 'boolean') return cfg.keepRealContent;
        return defaultKeepRealContent(section.type);
    }

    function sectionLayoutValue(cfg, key, fallback, min, max, decimals = false) {
        const value = Number(cfg[key] ?? fallback);
        const safeValue = Number.isFinite(value) ? value : fallback;
        const clamped = clamp(safeValue, min, max);
        return decimals ? Math.round(clamped * 100) / 100 : Math.round(clamped);
    }

    function applyPreviewSectionLayout(article, cfg, fullImage) {
        const collapsed = cfg.layoutCollapsed === true;
        const autoHeight = cfg.layoutAutoHeight === true;
        const height = sectionLayoutValue(cfg, 'sectionHeight', 420, 80, 1400);
        const minHeight = sectionLayoutValue(cfg, 'layoutMinHeight', 150, 0, 1400);
        const maxHeight = sectionLayoutValue(cfg, 'layoutMaxHeight', 0, 0, 2400);
        const width = sectionLayoutValue(cfg, 'layoutWidth', 100, 20, 140);
        const scale = sectionLayoutValue(cfg, 'layoutScale', 1, 0.25, 3, true);
        const paddingX = sectionLayoutValue(cfg, 'layoutPaddingX', 20, 0, 160);
        const paddingY = sectionLayoutValue(cfg, 'layoutPaddingY', 24, 0, 160);
        const marginBottom = sectionLayoutValue(cfg, 'layoutMarginBottom', 12, 0, 220);
        const aspectRatio = typeof cfg.layoutAspectRatio === 'string' ? cfg.layoutAspectRatio.trim() : '';

        article.classList.toggle('is-collapsed-layout', collapsed);
        article.classList.toggle('is-expanded-layout', cfg.layoutExpanded !== false && !collapsed);
        article.style.width = `${width}%`;
        article.style.transform = `scale(${scale})`;
        article.style.transformOrigin = 'top center';
        article.style.setProperty('padding', `${paddingY}px ${paddingX}px`, 'important');
        article.style.marginBottom = `${marginBottom}px`;
        article.style.setProperty('min-height', collapsed
            ? '72px'
            : (autoHeight ? `${minHeight}px` : `${height}px`), 'important');
        article.style.maxHeight = !collapsed && maxHeight ? `${maxHeight}px` : '';
        article.style.height = collapsed ? '72px' : '';
        article.style.setProperty('aspect-ratio', !collapsed && fullImage && aspectRatio ? aspectRatio : 'auto', 'important');
    }

    function syncConfigInspectorFields(cfg, keys) {
        keys.forEach((key) => {
            root.querySelectorAll(`[data-config-field="${key}"]`).forEach((field) => {
                if (field.type === 'checkbox') {
                    field.checked = Boolean(cfg[key]);
                } else {
                    field.value = cfg[key] ?? '';
                }
            });
        });
    }

    function attachSectionResizeHandles(article, section, cfg, fullImage) {
        if (section.sectionId !== selectedId || cfg.layoutCollapsed === true) return;

        const box = document.createElement('div');
        box.className = 'preview-section-resize-handles';
        box.innerHTML = `
            <button type="button" class="preview-section-resize-handle is-east" data-section-resize="east" aria-label="Cambiar ancho"></button>
            <button type="button" class="preview-section-resize-handle is-south" data-section-resize="south" aria-label="Cambiar alto"></button>
            <button type="button" class="preview-section-resize-handle is-corner" data-section-resize="corner" aria-label="Cambiar ancho y alto"></button>
        `;

        box.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
        });

        box.querySelectorAll('[data-section-resize]').forEach((handle) => {
            handle.addEventListener('pointerdown', (event) => {
                event.preventDefault();
                event.stopPropagation();

                selectedId = section.sectionId;
                selectedComponentId = null;

                const mode = handle.dataset.sectionResize;
                const parentRect = article.parentElement?.getBoundingClientRect();
                if (!parentRect || parentRect.width <= 0) return;

                const visualScale = sectionLayoutValue(cfg, 'layoutScale', 1, 0.25, 3, true);
                const drag = {
                    pointerId: event.pointerId,
                    startClientX: event.clientX,
                    startClientY: event.clientY,
                    startWidth: sectionLayoutValue(cfg, 'layoutWidth', 100, 20, 140),
                    startHeight: sectionLayoutValue(cfg, 'sectionHeight', 420, 80, 1400),
                    parentWidth: parentRect.width,
                    scale: visualScale || 1,
                    mode,
                };

                handle.setPointerCapture?.(event.pointerId);
                article.classList.add('is-resizing-layout');

                const move = (moveEvent) => {
                    if (moveEvent.pointerId !== drag.pointerId) return;
                    moveEvent.preventDefault();

                    cfg.layoutAutoHeight = false;
                    cfg.layoutCollapsed = false;
                    cfg.layoutExpanded = true;
                    cfg.layoutAspectRatio = '';

                    if (drag.mode === 'east' || drag.mode === 'corner') {
                        const deltaWidth = ((moveEvent.clientX - drag.startClientX) / (drag.parentWidth * drag.scale)) * 100;
                        cfg.layoutWidth = Math.round(clamp(drag.startWidth + deltaWidth, 20, 140));
                    }

                    if (drag.mode === 'south' || drag.mode === 'corner') {
                        const deltaHeight = (moveEvent.clientY - drag.startClientY) / drag.scale;
                        cfg.sectionHeight = Math.round(clamp(drag.startHeight + deltaHeight, 80, 1400));
                    }

                    applyPreviewSectionLayout(article, cfg, fullImage);
                    syncConfigInspectorFields(cfg, ['layoutWidth', 'sectionHeight', 'layoutAutoHeight', 'layoutCollapsed']);
                    setState('Cambios sin guardar');
                };

                const finish = (finishEvent) => {
                    if (finishEvent?.pointerId && finishEvent.pointerId !== drag.pointerId) return;
                    article.classList.remove('is-resizing-layout');
                    document.removeEventListener('pointermove', move);
                    document.removeEventListener('pointerup', finish);
                    document.removeEventListener('pointercancel', finish);
                    renderAll();
                };

                document.addEventListener('pointermove', move);
                document.addEventListener('pointerup', finish);
                document.addEventListener('pointercancel', finish);
            });
        });

        article.appendChild(box);
    }

    function renderPreview() {
        previewRoot.innerHTML = '';
        sortedSections().filter((section) => section.visible).forEach((section) => {
            const cfg = ensureSectionConfig(section);
            const article = document.createElement('article');
            article.className = `preview-section title-${cfg.titleSize || 'medium'}`;
            article.dataset.sectionId = String(section.sectionId);
            article.dataset.sectionType = section.type;
            article.dataset.activeLayer = cfg.activeLayer || 'background';
            article.classList.toggle('is-selected', section.sectionId === selectedId);
            article.style.textAlign = cfg.textAlign || 'center';

            const background = cfg.backgroundAsset || {};
            const titleAsset = cfg.titleAsset || {};
            const fullImage = isFullImageSection(section, cfg);
            const keepRealContent = sectionKeepsRealContent(section, cfg);

            /*
            En modo imagen completa solo puede existir una fuente visual
            principal en la Vista Rápida.

            Prioridad:
            1. titleAsset
            2. backgroundAsset como respaldo
            */
            const fullImageUsesTitle =
                fullImage &&
                Boolean(titleAsset.url) &&
                cfg.showTitleAsset !== false;

            const fullImageUsesBackground =
                fullImage &&
                !fullImageUsesTitle &&
                Boolean(background.url) &&
                cfg.showBackgroundLayer !== false;

            article.classList.toggle('is-full-image', fullImage);
            article.classList.toggle(
                'hide-real-content',
                fullImage && !keepRealContent
            );

            applyPreviewSectionLayout(article, cfg, fullImage);

            if (cfg.textColor) {
                article.style.color = cfg.textColor;
            }

            /*
            El video de fondo no se crea cuando titleAsset ya es
            la imagen completa principal.
            */
            if (
                !fullImageUsesTitle &&
                cfg.showBackgroundLayer !== false &&
                background.url &&
                background.isVideo
            ) {
                const video = document.createElement('video');
                video.className = 'preview-section-media';
                video.src = background.url;
                video.autoplay = true;
                video.muted = true;
                video.loop = true;
                video.playsInline = true;

                video.style.opacity = String(
                    clamp(cfg.backgroundOpacity ?? 1, 0, 1)
                );

                video.style.objectFit =
                    cfg.backgroundFit === 'cover'
                        ? 'cover'
                        : 'contain';

                video.style.objectPosition =
                    `${clamp(
                        effectiveBackgroundValue(cfg, 'backgroundX') ?? 50,
                        0,
                        100
                    )}% ${clamp(
                        effectiveBackgroundValue(cfg, 'backgroundY') ?? 50,
                        0,
                        100
                    )}%`;

                video.style.filter =
                    `brightness(${clamp(
                        cfg.backgroundBrightness ?? 1,
                        0.35,
                        1.75
                    )}) blur(${clamp(
                        cfg.backgroundBlur ?? 0,
                        0,
                        12
                    )}px)`;

                article.appendChild(video);
            }

            /*
            La capa de fondo se oculta cuando titleAsset es la imagen
            completa seleccionada.
            */
            const bgLayer = document.createElement('div');
            bgLayer.className = 'preview-section-bg';

            const hideBackgroundLayer =
                cfg.showBackgroundLayer === false ||
                fullImageUsesTitle;

            bgLayer.classList.toggle(
                'is-hidden',
                hideBackgroundLayer
            );

            if (!hideBackgroundLayer) {
                setBackgroundStyles(
                    bgLayer,
                    cfg,
                    background
                );
            }

            attachBackgroundDrag(
                article,
                bgLayer,
                section,
                cfg
            );

            article.appendChild(bgLayer);

            /*
            La decoración conserva su comportamiento actual.
            */
            const decorLayer = document.createElement('div');
            decorLayer.className =
                'preview-layer preview-decor-layer';
            decorLayer.dataset.layer = 'decor';
            decorLayer.textContent = decorText(cfg.decorStyle);

            setLayerStyles(
                decorLayer,
                cfg,
                'decor'
            );

            attachLayerDrag(
                article,
                decorLayer,
                section,
                cfg,
                'decor'
            );

            article.appendChild(decorLayer);

            /*
            La capa de título:
            - muestra el recurso pequeño en modo normal;
            - muestra el recurso a tamaño completo cuando full-image
              utiliza titleAsset;
            - se oculta cuando full-image utiliza backgroundAsset.
            */
            const titleLayer = document.createElement('div');
            titleLayer.className =
                'preview-layer preview-title-layer';
            titleLayer.dataset.layer = 'title';

            const renderTitleAsset =
                Boolean(titleAsset.url) &&
                cfg.showTitleAsset !== false &&
                (!fullImage || fullImageUsesTitle);

            if (renderTitleAsset) {
                titleLayer.insertAdjacentHTML(
                    'beforeend',
                    titleAsset.isVideo
                        ? `<video class="preview-title-asset" src="${titleAsset.url}" autoplay muted loop playsinline></video>`
                        : `<img class="preview-title-asset" src="${titleAsset.url}" alt="">`
                );
            }

            if (
                !fullImage &&
                cfg.showTextTitle !== false
            ) {
                const title = document.createElement('h2');
                title.textContent = section.title || '';
                titleLayer.appendChild(title);
            }

            setLayerStyles(
                titleLayer,
                cfg,
                'title'
            );

            if (fullImageUsesTitle) {
                titleLayer.classList.remove('is-hidden');
                titleLayer.classList.add(
                    'is-full-image-title-layer'
                );
            } else if (fullImageUsesBackground) {
                titleLayer.classList.add('is-hidden');
                titleLayer.classList.remove(
                    'is-full-image-title-layer'
                );
            } else if (fullImage) {
                titleLayer.classList.add('is-hidden');
                titleLayer.classList.remove(
                    'is-full-image-title-layer'
                );
            } else {
                titleLayer.classList.remove(
                    'is-full-image-title-layer'
                );
            }

            attachLayerDrag(
                article,
                titleLayer,
                section,
                cfg,
                'title'
            );

            article.appendChild(titleLayer);

            const textLayer = document.createElement('div');
            textLayer.className = 'preview-layer preview-text-layer';
            textLayer.dataset.layer = 'text';
            const copy = document.createElement('div');
            copy.className = 'preview-real-data';
            copy.innerHTML = sectionPreviewHtml(section, cfg);
            if (realContentSections.has(section.type)) {
                applyRealContentStyles(copy, cfg, section.type);
            }
            textLayer.appendChild(copy);
            setLayerStyles(textLayer, cfg, 'text');
            if (fullImage && !keepRealContent) textLayer.classList.add('is-hidden');
            attachLayerDrag(article, textLayer, section, cfg, 'text');
            article.appendChild(textLayer);
            ensureCustomLayers(cfg).forEach((layer) => {
                const layerEl = document.createElement('div');
                layerEl.className = 'preview-layer preview-custom-layer';
                layerEl.dataset.customLayerId = layer.id;
                layerEl.classList.toggle('is-active-custom', cfg.activeLayer === `custom:${layer.id}`);
                if (layer.kind === 'image' && layer.asset?.url) {
                    layerEl.innerHTML = `<img class="preview-free-media" src="${layer.asset.url}" alt="">`;
                } else if (layer.kind === 'video' && layer.asset?.url) {
                    layerEl.innerHTML = `<video class="preview-free-media" src="${layer.asset.url}" autoplay muted loop playsinline></video>`;
                } else {
                    layerEl.innerHTML = `<span class="preview-free-text">${escapeHtml(layer.text || 'Texto editable')}</span>`;
                }
                const media = layerEl.querySelector('.preview-free-media');
                if (media) media.style.objectFit = layer.fit || 'contain';
                setCustomLayerStyles(layerEl, layer);
                attachCustomLayerDrag(article, layerEl, section, cfg, layer);
                article.appendChild(layerEl);
            });
            renderBuilderComponents(article, section);
            attachSectionResizeHandles(article, section, cfg, fullImage);
            article.addEventListener('click', () => {
                selectedId = section.sectionId;
                selectedComponentId = null;
                renderAll();
            });
            article.addEventListener('dragover', (event) => {
                if (event.dataTransfer.types.includes('application/x-editor-asset')) event.preventDefault();
            });
            article.addEventListener('drop', (event) => {
                const payload = event.dataTransfer.getData('application/x-editor-asset');
                if (!payload) return;
                event.preventDefault();
                selectedId = section.sectionId;
                assignAssetRef(JSON.parse(payload), 'CAPA_LIBRE', section).catch((error) => setState(error.message));
            });
            previewRoot.appendChild(article);
        });
    }

    function attachBackgroundDrag(article, bgLayer, section, cfg) {
        let dragging = null;
        bgLayer.addEventListener('pointerdown', (event) => {
            if (!cfg.backgroundAsset?.url) return;
            selectedId = section.sectionId;
            cfg.activeLayer = 'background';
            dragging = {
                x: event.clientX,
                y: event.clientY,
                startX: clamp(effectiveBackgroundValue(cfg, 'backgroundX') ?? 50, 0, 100),
                startY: clamp(effectiveBackgroundValue(cfg, 'backgroundY') ?? 50, 0, 100),
                width: Math.max(article.clientWidth, 1),
                height: Math.max(article.clientHeight, 1),
            };
            bgLayer.setPointerCapture(event.pointerId);
        });
        bgLayer.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            const deltaX = ((event.clientX - dragging.x) / dragging.width) * 100;
            const deltaY = ((event.clientY - dragging.y) / dragging.height) * 100;
            setBackgroundValue(cfg, 'backgroundX', Math.round(clamp(dragging.startX + deltaX, 0, 100)));
            setBackgroundValue(cfg, 'backgroundY', Math.round(clamp(dragging.startY + deltaY, 0, 100)));
            setBackgroundStyles(bgLayer, cfg, cfg.backgroundAsset || {});
            const xField = root.querySelector('[data-config-field="backgroundX"]');
            const yField = root.querySelector('[data-config-field="backgroundY"]');
            if (xField) xField.value = effectiveBackgroundValue(cfg, 'backgroundX');
            if (yField) yField.value = effectiveBackgroundValue(cfg, 'backgroundY');
            setState('Cambios sin guardar');
        });
        bgLayer.addEventListener('pointerup', () => { dragging = null; });
        bgLayer.addEventListener('pointercancel', () => { dragging = null; });
    }

    function attachLayerDrag(article, layerEl, section, cfg, layer) {
        let dragging = null;
        layerEl.addEventListener('click', (event) => {
            event.stopPropagation();
            selectedId = section.sectionId;
            cfg.activeLayer = layer;
            renderAll();
        });
        layerEl.addEventListener('pointerdown', (event) => {
            if (layerValue(cfg, layer, 'locked') === true) return;
            event.stopPropagation();
            selectedId = section.sectionId;
            cfg.activeLayer = layer;
            dragging = {
                x: event.clientX,
                y: event.clientY,
                startX: clamp(layerValue(cfg, layer, 'x'), layerBounds.min, layerBounds.max),
                startY: clamp(layerValue(cfg, layer, 'y'), layerBounds.min, layerBounds.max),
                width: Math.max(article.clientWidth, 1),
                height: Math.max(article.clientHeight, 1),
            };
            layerEl.setPointerCapture(event.pointerId);
        });
        layerEl.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            const deltaX = ((event.clientX - dragging.x) / dragging.width) * 100;
            const deltaY = ((event.clientY - dragging.y) / dragging.height) * 100;
            setLayerValue(cfg, layer, 'x', Math.round(clamp(dragging.startX + deltaX, layerBounds.min, layerBounds.max)));
            setLayerValue(cfg, layer, 'y', Math.round(clamp(dragging.startY + deltaY, layerBounds.min, layerBounds.max)));
            setLayerStyles(layerEl, cfg, layer);
            updateLayerFields(cfg);
            setState('Cambios sin guardar');
        });
        layerEl.addEventListener('pointerup', () => { dragging = null; });
        layerEl.addEventListener('pointercancel', () => { dragging = null; });
    }

    function attachCustomLayerDrag(article, layerEl, section, cfg, layer) {
        let dragging = null;
        layerEl.addEventListener('click', (event) => {
            event.stopPropagation();
            selectedId = section.sectionId;
            cfg.activeLayer = `custom:${layer.id}`;
            renderAll();
        });
        layerEl.addEventListener('pointerdown', (event) => {
            if (layer.locked === true) return;
            event.stopPropagation();
            selectedId = section.sectionId;
            cfg.activeLayer = `custom:${layer.id}`;
            dragging = {
                x: event.clientX,
                y: event.clientY,
                startX: clamp(layer.x ?? 50, layerBounds.min, layerBounds.max),
                startY: clamp(layer.y ?? 50, layerBounds.min, layerBounds.max),
                width: Math.max(article.clientWidth, 1),
                height: Math.max(article.clientHeight, 1),
            };
            layerEl.setPointerCapture(event.pointerId);
        });
        layerEl.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            const deltaX = ((event.clientX - dragging.x) / dragging.width) * 100;
            const deltaY = ((event.clientY - dragging.y) / dragging.height) * 100;
            layer.x = Math.round(clamp(dragging.startX + deltaX, layerBounds.min, layerBounds.max));
            layer.y = Math.round(clamp(dragging.startY + deltaY, layerBounds.min, layerBounds.max));
            setCustomLayerStyles(layerEl, layer);
            updateLayerFields(cfg);
            renderCustomLayerList(cfg);
            setState('Cambios sin guardar');
        });
        layerEl.addEventListener('pointerup', () => { dragging = null; });
        layerEl.addEventListener('pointercancel', () => { dragging = null; });
    }

    function updateLayerFields(cfg) {
        const layer = cfg.activeLayer || 'background';
        const custom = customLayerByActive(cfg);
        root.querySelectorAll('[data-layer-field]').forEach((field) => {
            const key = field.dataset.layerField;
            if (key === 'scale') {
                field.min = custom ? '0.35' : '0.5';
                field.max = custom ? '3' : '2.2';
            }
            if (key === 'rotation') {
                field.min = custom ? '-180' : '-45';
                field.max = custom ? '180' : '45';
            }
            if (key === 'width') {
                field.min = custom ? '8' : '12';
                field.max = custom ? '120' : '100';
            }
            field.disabled = layer === 'background';
            if (field.type === 'checkbox') {
                field.checked = custom ? customLayerValue(custom, key) !== false : layerValue(cfg, layer, key) !== false;
            } else {
                field.value = custom ? customLayerValue(custom, key) : layerValue(cfg, layer, key);
            }
        });
        const customText = root.querySelector('[data-custom-layer-text]');
        const customName = root.querySelector('[data-custom-layer-name]');
        const customFit = root.querySelector('[data-custom-layer-fit]');
        if (customText) {
            customText.disabled = !custom || custom.kind !== 'text';
            customText.value = custom?.text || '';
        }
        if (customName) {
            customName.disabled = !custom;
            customName.value = custom?.name || '';
        }
        if (customFit) {
            customFit.disabled = !custom || custom.kind === 'text';
            customFit.value = custom?.fit || 'contain';
        }
        root.querySelectorAll('[data-layer-action="duplicate"], [data-layer-action="delete"]').forEach((button) => {
            button.disabled = !custom;
        });
    }

    function resetLayer(cfg, layer) {
        const custom = customLayerByActive(cfg);
        if (custom) {
            Object.assign(custom, normalizeCustomLayer({ ...custom, x: 50, y: 50, scale: 1, opacity: 1, rotation: 0, locked: false, width: custom.kind === 'text' ? 64 : 42, align: 'center' }));
            return;
        }
        const defaults = layerDefaults(layer);
        Object.entries(defaults).forEach(([key, value]) => setLayerValue(cfg, layer, key, value));
    }

    function applyLayerPreset(cfg, layer, preset) {
        const custom = customLayerByActive(cfg);
        const presets = {
            centered: { x: 50, y: layer === 'decor' ? 12 : 50, scale: 1, rotation: 0, opacity: layer === 'decor' ? 0.42 : 1, width: layer === 'decor' ? 36 : 72, align: 'center' },
            upper: { x: 50, y: layer === 'decor' ? 10 : 28, scale: 0.9, rotation: 0, opacity: layer === 'decor' ? 0.5 : 1, width: 66, align: 'center' },
            lower: { x: 50, y: 72, scale: 0.9, rotation: 0, opacity: layer === 'decor' ? 0.36 : 0.92, width: 72, align: 'center' },
            diagonal: { x: 38, y: 48, scale: 1.05, rotation: -8, opacity: layer === 'decor' ? 0.38 : 0.9, width: 48, align: 'left' },
        };
        if (custom) {
            Object.entries(presets[preset] || presets.centered).forEach(([key, value]) => setCustomLayerValue(custom, key, value));
            custom.visible = true;
            return;
        }
        Object.entries(presets[preset] || presets.centered).forEach(([key, value]) => setLayerValue(cfg, layer, key, value));
        setLayerValue(cfg, layer, 'visible', true);
    }

    function moveLayerZ(cfg, layer, direction) {
        const custom = customLayerByActive(cfg);
        if (custom) {
            custom.z = clamp((Number(custom.z) || 3) + direction, 1, 12);
            return;
        }
        const current = clamp(layerValue(cfg, layer, 'z'), 1, 5);
        setLayerValue(cfg, layer, 'z', clamp(current + direction, 1, 5));
    }

    function layerListItems(cfg) {
        const base = [
            {
                id: 'background',
                label: 'Fondo',
                type: 'Base',
                z: 0,
                visible: cfg.showBackgroundLayer !== false,
                locked: true,
                canLock: false,
                canMove: false,
            },
            {
                id: 'title',
                label: 'Titulo',
                type: 'Texto/imagen',
                z: layerValue(cfg, 'title', 'z'),
                visible: layerValue(cfg, 'title', 'visible') !== false,
                locked: layerValue(cfg, 'title', 'locked') === true,
                canLock: true,
                canMove: true,
            },
            {
                id: 'text',
                label: 'Contenido real',
                type: 'Datos',
                z: layerValue(cfg, 'text', 'z'),
                visible: layerValue(cfg, 'text', 'visible') !== false,
                locked: layerValue(cfg, 'text', 'locked') === true,
                canLock: true,
                canMove: true,
            },
            {
                id: 'decor',
                label: 'Decoracion',
                type: 'Adorno',
                z: layerValue(cfg, 'decor', 'z'),
                visible: layerValue(cfg, 'decor', 'visible') !== false,
                locked: layerValue(cfg, 'decor', 'locked') === true,
                canLock: true,
                canMove: true,
            },
        ];
        const custom = ensureCustomLayers(cfg).map((layer) => ({
            id: `custom:${layer.id}`,
            label: layer.name || 'Capa libre',
            type: layer.kind === 'text' ? 'Texto libre' : layer.kind === 'video' ? 'Video libre' : 'Imagen libre',
            z: layer.z || 3,
            visible: layer.visible !== false,
            locked: layer.locked === true,
            canLock: true,
            canMove: true,
            custom: layer,
        }));
        return [...custom, ...base].sort((a, b) => Number(b.z || 0) - Number(a.z || 0));
    }

    function setLayerVisibility(cfg, layerId) {
        if (layerId === 'background') {
            cfg.showBackgroundLayer = cfg.showBackgroundLayer === false;
            return;
        }
        if (isCustomLayer(layerId)) {
            cfg.customLayers = ensureCustomLayers(cfg);
            const custom = cfg.customLayers.find((layer) => `custom:${layer.id}` === layerId);
            if (custom) custom.visible = custom.visible === false;
            return;
        }
        setLayerValue(cfg, layerId, 'visible', layerValue(cfg, layerId, 'visible') === false);
    }

    function setLayerLocked(cfg, layerId) {
        if (layerId === 'background') return;
        if (isCustomLayer(layerId)) {
            cfg.customLayers = ensureCustomLayers(cfg);
            const custom = cfg.customLayers.find((layer) => `custom:${layer.id}` === layerId);
            if (custom) custom.locked = custom.locked !== true;
            return;
        }
        setLayerValue(cfg, layerId, 'locked', layerValue(cfg, layerId, 'locked') !== true);
    }

    function moveLayerFromList(cfg, layerId, direction) {
        cfg.activeLayer = layerId;
        if (layerId === 'background') return;
        moveLayerZ(cfg, layerId, direction);
    }

    function setLayerTreeZ(cfg, layerId, value) {
        if (!cfg || !layerId || layerId === 'background') return;
        if (isCustomLayer(layerId)) {
            cfg.customLayers = ensureCustomLayers(cfg);
            const id = String(layerId).replace('custom:', '');
            const custom = cfg.customLayers.find((layer) => layer.id === id);
            if (custom) custom.z = clamp(value, 1, 12);
            return;
        }
        setLayerValue(cfg, layerId, 'z', clamp(value, 1, 5));
    }

    function reorderLayerTreeByDrop(section, cfg, draggedLayerId, targetLayerId) {
        if (!section || !cfg || !draggedLayerId || !targetLayerId || draggedLayerId === targetLayerId) return false;
        const ordered = layerListItems(cfg).filter((layer) => layer.canMove);
        const from = ordered.findIndex((layer) => layer.id === draggedLayerId);
        const to = ordered.findIndex((layer) => layer.id === targetLayerId);
        if (from < 0 || to < 0) return false;
        const [dragged] = ordered.splice(from, 1);
        ordered.splice(to, 0, dragged);
        ordered.forEach((layer, index) => {
            setLayerTreeZ(cfg, layer.id, ordered.length - index);
        });
        selectedId = section.sectionId;
        selectedComponentId = null;
        cfg.activeLayer = draggedLayerId;
        setState('Orden de capas actualizado');
        renderAll();
        return true;
    }

    function reorderComponentTreeByDrop(draggedComponentId, targetComponentId) {
        if (!draggedComponentId || !targetComponentId || draggedComponentId === targetComponentId) return false;
        const dragged = builderComponentById(draggedComponentId);
        const target = builderComponentById(targetComponentId);
        if (!dragged || !target || Number(dragged.sectionId) !== Number(target.sectionId)) return false;
        const ordered = builderComponents
            .filter((component) => Number(component.sectionId) === Number(dragged.sectionId))
            .sort((a, b) => (a.zIndex || 0) - (b.zIndex || 0) || (a.id || 0) - (b.id || 0));
        const from = ordered.findIndex((component) => Number(component.id) === Number(draggedComponentId));
        const to = ordered.findIndex((component) => Number(component.id) === Number(targetComponentId));
        if (from < 0 || to < 0) return false;
        const [item] = ordered.splice(from, 1);
        ordered.splice(to, 0, item);
        ordered.forEach((component, index) => {
            component.zIndex = clamp((index + 1) * 5, 1, 100);
        });
        selectedId = dragged.sectionId;
        selectedComponentId = dragged.id;
        setState('Guardando orden de componentes...');
        renderAll();
        Promise.all(
            ordered
                .filter((component) => component.id)
                .map((component) => saveBuilderComponent(component, { skipRealRefresh: true }))
        )
            .then(() => {
                setState('Orden de componentes guardado');
                refreshRealPreview();
            })
            .catch((error) => setState(error.message));
        return true;
    }

    function treePayloadFromRow(row) {
        if (!row) return null;
        return {
            action: row.dataset.treeAction || '',
            sectionId: Number(row.dataset.treeSectionId || 0),
            layerId: row.dataset.treeLayerId || '',
            componentId: Number(row.dataset.treeComponentId || 0),
        };
    }

    function compatibleTreeDrop(source, target) {
        if (!source || !target || source.action !== target.action) return false;
        if (!['layer', 'component'].includes(source.action)) return false;
        if (Number(source.sectionId) !== Number(target.sectionId)) return false;
        if (source.action === 'layer') return Boolean(source.layerId && target.layerId && source.layerId !== target.layerId);
        return Boolean(source.componentId && target.componentId && source.componentId !== target.componentId);
    }

    function applyComponentTreeDrop(source, target) {
        if (!compatibleTreeDrop(source, target)) return false;
        if (source.action === 'component') {
            return reorderComponentTreeByDrop(source.componentId, target.componentId);
        }
        const section = config.sections.find((item) => Number(item.sectionId) === Number(source.sectionId));
        const cfg = section ? ensureSectionConfig(section) : null;
        return reorderLayerTreeByDrop(section, cfg, source.layerId, target.layerId);
    }

    function addCustomLayer(section, layer) {
        const cfg = ensureSectionConfig(section);
        const clean = normalizeCustomLayer(layer);
        cfg.customLayers.unshift(clean);
        cfg.customLayers = cfg.customLayers.slice(0, 60);
        cfg.activeLayer = `custom:${clean.id}`;
        selectedId = section.sectionId;
        setState('Capa libre agregada');
        renderAll();
    }

    function deleteActiveCustomLayer(cfg) {
        const custom = customLayerByActive(cfg);
        if (!custom) return false;
        cfg.customLayers = ensureCustomLayers(cfg).filter((layer) => layer.id !== custom.id);
        cfg.activeLayer = 'title';
        return true;
    }

    function duplicateActiveCustomLayer(cfg) {
        const custom = customLayerByActive(cfg);
        if (!custom) return false;
        const copy = normalizeCustomLayer({
            ...custom,
            id: customLayerId(),
            name: `${custom.name || 'Capa'} copia`,
            x: Number(custom.x || 50) + 5,
            y: Number(custom.y || 50) + 5,
        });
        cfg.customLayers.unshift(copy);
        cfg.activeLayer = `custom:${copy.id}`;
        return true;
    }

    function renderCustomLayerList(cfg) {
        const list = root.querySelector('[data-custom-layer-list]');
        if (!list) return;
        const layers = layerListItems(cfg);
        list.innerHTML = '';
        if (!layers.length) {
            list.innerHTML = '<p class="muted">Sin capas en esta seccion.</p>';
            return;
        }
        layers.forEach((layer) => {
            const item = document.createElement('article');
            item.className = 'custom-layer-item';
            item.classList.toggle('is-active', cfg.activeLayer === layer.id);
            item.classList.toggle('is-muted', layer.visible === false);
            item.innerHTML = `
                <button type="button" class="layer-row-main" data-layer-list-action="select" data-layer-id="${escapeHtml(layer.id)}">
                    <strong>${escapeHtml(layer.label)}</strong>
                    <span>${escapeHtml(layer.type)} - z ${Number(layer.z || 0)}</span>
                </button>
                <div class="layer-row-tools">
                    <button type="button" data-layer-list-action="toggle" data-layer-id="${escapeHtml(layer.id)}">${layer.visible === false ? 'Mostrar' : 'Ocultar'}</button>
                    <button type="button" data-layer-list-action="lock" data-layer-id="${escapeHtml(layer.id)}" ${layer.canLock ? '' : 'disabled'}>${layer.locked ? 'Abrir' : 'Bloquear'}</button>
                    <button type="button" data-layer-list-action="back" data-layer-id="${escapeHtml(layer.id)}" ${layer.canMove ? '' : 'disabled'}>Atras</button>
                    <button type="button" data-layer-list-action="front" data-layer-id="${escapeHtml(layer.id)}" ${layer.canMove ? '' : 'disabled'}>Frente</button>
                </div>
            `;
            list.appendChild(item);
        });
    }

    function fillProperties() {
        const theme = config.theme || {};
        root.querySelectorAll('[data-theme-field]').forEach((field) => {
            const value = theme[field.dataset.themeField] || '';
            if (field.type === 'color') {
                field.value = value || field.value;
            } else {
                field.value = value;
            }
        });

        const section = selectedSection();
        sectionProps.classList.toggle('is-empty', !section);
        updateAssetDetailButtons();
        if (!section) return;
        root.querySelectorAll('[data-section-field]').forEach((field) => {
            const key = field.dataset.sectionField;
            if (field.type === 'checkbox') {
                field.checked = Boolean(section[key]);
            } else {
                field.value = section[key] ?? '';
            }
        });
        root.querySelectorAll('[data-config-field]').forEach((field) => {
            const cfg = ensureSectionConfig(section);
            const key = field.dataset.configField;
            if (field.type === 'checkbox') {
                field.checked = cfg[key] !== false;
            } else if (field.type === 'color') {
                field.value = cfg[key] || '#263126';
            } else if (['backgroundX', 'backgroundY', 'backgroundScale'].includes(key)) {
                field.value = effectiveBackgroundValue(cfg, key) ?? '';
            } else {
                field.value = cfg[key] ?? '';
            }
        });
        root.querySelectorAll('[data-layer-select]').forEach((button) => {
            button.classList.toggle('is-active', ensureSectionConfig(section).activeLayer === button.dataset.layerSelect);
        });
        const layerControls = root.querySelector('.layer-controls');
        if (layerControls) layerControls.hidden = ensureSectionConfig(section).activeLayer === 'background';
        const presetSelect = root.querySelector('[data-layer-preset]');
        if (presetSelect) presetSelect.value = '';
        updateLayerFields(ensureSectionConfig(section));
        renderCustomLayerList(ensureSectionConfig(section));
        fillRealContentProperties();
        fillComponentProperties();
        updateUniversalInspector();
    }


    const editorUi = {
        mode: 'simple',
        panel: 'design',
    };

    function ensureEditorUiIntegrity() {
        /*
         * S02-P01 — Integridad de herramientas del editor.
         *
         * El HTML ya incluye los grupos de panel, pero esta función
         * conserva compatibilidad con templates antiguos y evita que
         * todos los controles queden ocultos si falta un atributo.
         */
        root.dataset.editorMode =
            root.dataset.editorMode || editorUi.mode;

        root.dataset.editorPanel =
            root.dataset.editorPanel || editorUi.panel;

        const groups = [
            ...root.querySelectorAll(
                '.properties-panel > .property-group'
            ),
        ];

        groups.forEach((group, index) => {
            if (!group.dataset.editorGroup) {
                if (
                    group.hasAttribute('data-universal-inspector') ||
                    group.hasAttribute('data-section-properties') ||
                    index <= 1
                ) {
                    group.dataset.editorGroup = 'design';
                } else if (
                    group.classList.contains('quick-content-panel') ||
                    group.querySelector(
                        '[data-content-form], [data-guest-form]'
                    )
                ) {
                    group.dataset.editorGroup = 'content';
                } else if (
                    group.querySelector(
                        '[data-asset-form], [data-asset-list]'
                    )
                ) {
                    group.dataset.editorGroup = 'assets';
                } else {
                    group.dataset.editorGroup = 'content';
                }
            }
        });

        const inspector = root.querySelector(
            '[data-universal-inspector]'
        );

        if (inspector) {
            inspector.dataset.editorPersistent = 'true';
        }

        const missingPanels = [
            'design',
            'content',
            'assets',
        ].filter((panel) => {
            return !root.querySelector(
                `[data-editor-group="${panel}"]`
            );
        });

        if (missingPanels.length) {
            console.warn(
                'DIRTEC Editor: faltan grupos de propiedades:',
                missingPanels
            );
        }
    }

    const easySectionPresets = {
        PORTADA: { height: 620, titleY: 36, textY: 70, titleWidth: 88, textWidth: 90 },
        PADRES_PADRINOS: { height: 520, titleY: 16, textY: 56, titleWidth: 86, textWidth: 92 },
        CUENTA_REGRESIVA: { height: 620, titleY: 16, textY: 58, titleWidth: 82, textWidth: 90 },
        DETALLES: { height: 620, titleY: 14, textY: 58, titleWidth: 88, textWidth: 94 },
        DRESS_CODE: { height: 620, titleY: 14, textY: 58, titleWidth: 88, textWidth: 94 },
        ITINERARIO: { height: 560, titleY: 14, textY: 58, titleWidth: 86, textWidth: 90 },
        ALBUM: { height: 560, titleY: 14, textY: 58, titleWidth: 86, textWidth: 94 },
        MENU: { height: 620, titleY: 14, textY: 58, titleWidth: 86, textWidth: 92 },
        REGALOS: { height: 620, titleY: 14, textY: 58, titleWidth: 86, textWidth: 92 },
        ALBUM_COMPARTIDO: { height: 620, titleY: 14, textY: 58, titleWidth: 86, textWidth: 90 },
        RSVP: { height: 680, titleY: 12, textY: 56, titleWidth: 86, textWidth: 94 },
    };

    function selectedPreset() {
        const section = selectedSection();
        return easySectionPresets[section?.type] || {
            height: 520,
            titleY: 16,
            textY: 58,
            titleWidth: 86,
            textWidth: 90,
        };
    }

    function applyEasyLayout({ fullImage = false } = {}) {
        const section = selectedSection();
        if (!section) {
            setState('Selecciona una sección.');
            return;
        }

        const cfg = ensureSectionConfig(section);
        const preset = selectedPreset();
        const keepRealContent = fullImage ? defaultKeepRealContent(section.type) : true;

        Object.assign(cfg, {
            layoutMode: fullImage ? 'full-image' : 'normal',
            keepRealContent,
            sectionHeight: preset.height,
            layoutAutoHeight: false,
            layoutExpanded: true,
            layoutCollapsed: false,
            layoutWidth: 100,
            layoutScale: 1,
            layoutPaddingX: fullImage ? 0 : 20,
            layoutPaddingY: fullImage ? 0 : 24,
            layoutMarginBottom: 12,
            layoutMinHeight: fullImage ? preset.height : 150,
            layoutMaxHeight: 0,
            layoutAspectRatio: fullImage ? '' : '',
            backgroundOpacity: 1,
            backgroundFit: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundBrightness: 1,
            backgroundBlur: 0,
            backgroundX: 50,
            backgroundY: 50,
            backgroundScale: 1,
            backgroundXMobile: 50,
            backgroundYMobile: 50,
            backgroundScaleMobile: 1,
            backgroundXTablet: 50,
            backgroundYTablet: 50,
            backgroundScaleTablet: 1,
            backgroundXDesktop: 50,
            backgroundYDesktop: 50,
            backgroundScaleDesktop: 1,
            showBackgroundLayer: true,
            titleX: 50,
            titleY: preset.titleY,
            titleScale: 1,
            titleOpacity: 1,
            titleRotation: 0,
            titleWidth: preset.titleWidth,
            titleAlign: 'center',
            titleVisible: !fullImage,
            titleLocked: false,
            titleZ: 3,
            textX: 50,
            textY: preset.textY,
            textScale: 1,
            textOpacity: 1,
            textRotation: 0,
            textWidth: preset.textWidth,
            textAlignLayer: 'center',
            textVisible: keepRealContent,
            textLocked: false,
            textZ: 4,
            decorVisible: false,
            showTextTitle: !fullImage,
            showTitleAsset: false,
            activeLayer: keepRealContent ? 'text' : 'background',
        });
        cfg.realContent = normalizeRealContentConfig({
            ...(cfg.realContent || {}),
            x: 50,
            y: fullImage ? 50 : 50,
            width: fullImage ? 94 : 100,
            scale: 1,
            opacity: 1,
            layout: 'grid',
        }, section.type);

        setState(
            fullImage
                ? (keepRealContent
                    ? 'Imagen completa con contenido real'
                    : 'Imagen completa sin contenido encima')
                : 'Distribución reparada'
        );
        renderAll();
    }

    function updateRangeReadouts() {
        root.querySelectorAll('input[type="range"]').forEach((input) => {
            let output = input.parentElement?.querySelector('.range-readout');
            if (!output) {
                output = document.createElement('output');
                output.className = 'range-readout';
                input.parentElement?.appendChild(output);
            }
            output.value = input.value;
            output.textContent = input.value;
        });
    }

    function editorContextLabel() {
        const component = selectedComponent();
        if (component) {
            const labels = {
                TEXTO: 'Texto',
                IMAGEN: 'Imagen',
                BOTON: 'Botón',
            };
            return {
                title: labels[component.tipo] || 'Componente',
                help: 'Edita únicamente las propiedades del componente seleccionado.',
                panel: 'design',
            };
        }

        const section = selectedSection();
        if (!section) {
            return {
                title: 'Invitación',
                help: 'Selecciona una sección o un elemento visible.',
                panel: 'design',
            };
        }

        const cfg = ensureSectionConfig(section);
        const inspectorTarget = inspectorTargetType();

        if (inspectorTarget === 'real' && realContentSections.has(section.type)) {
            return {
                title: `Contenido · ${section.title || section.type}`,
                help: 'Controla tarjetas, fotos, dirección, botón y mapa.',
                panel: 'design',
            };
        }

        if (inspectorTarget === 'layer') {
            return {
                title: `Capa · ${section.title || section.type}`,
                help: `Capa activa: ${cfg.activeLayer || 'fondo'}.`,
                panel: 'design',
            };
        }

        return {
            title: section.title || section.type || 'Sección',
            help: currentPreviewMode === 'real'
                ? 'La Vista Real es la referencia visual de publicación.'
                : 'Diseño rápido sirve para estructura, fondos, capas y componentes.',
            panel: 'design',
        };
    }

    function updateEditorContextCard() {
        const context = editorContextLabel();
        const title = root.querySelector('[data-editor-context-title]');
        const help = root.querySelector('[data-editor-context-help]');
        const openButton = root.querySelector('[data-editor-context-open]');

        if (title) title.textContent = context.title;
        if (help) help.textContent = context.help;
        if (openButton) {
            openButton.dataset.targetPanel = context.panel;
            openButton.textContent =
                editorUi.panel === context.panel
                    ? 'Controles abiertos'
                    : 'Ver controles';
        }
    }

    function setEditorPanel(panel) {
        editorUi.panel = panel;
        root.dataset.editorPanel = panel;
        root.querySelectorAll('[data-editor-panel-button]').forEach((button) => {
            button.classList.toggle(
                'is-active',
                button.dataset.editorPanelButton === panel
            );
        });
        updateEditorContextCard();
    }

    function setEditorMode(mode) {
        editorUi.mode = mode;
        root.dataset.editorMode = mode;
        root.querySelectorAll('[data-editor-mode]').forEach((button) => {
            button.classList.toggle(
                'is-active',
                button.dataset.editorMode === mode
            );
        });
        setState(mode === 'simple' ? 'Modo fácil' : 'Modo avanzado');
        updateEditorContextCard();
    }

    function installSimplifiedEditorUi() {
        /*
         * S02-P02
         * La barra principal ahora viene renderizada desde Django.
         * Se conserva este fallback para templates anteriores, pero
         * la función SIEMPRE continúa para conectar sus listeners.
         */
        let toolbar = root.querySelector('[data-simple-editor-toolbar]');

        if (!toolbar) {
            const propertiesPanel = root.querySelector('.properties-panel');
            const panelHeading = propertiesPanel?.querySelector(':scope > .panel-heading');

            if (propertiesPanel && panelHeading) {
                toolbar = document.createElement('div');
                toolbar.className = 'simple-editor-toolbar';
                toolbar.dataset.simpleEditorToolbar = '';
                toolbar.innerHTML = `
                    <div class="editor-mode-switch" aria-label="Nivel de edición">
                        <button type="button" class="is-active" data-editor-mode="simple">Fácil</button>
                        <button type="button" data-editor-mode="advanced">Avanzado</button>
                    </div>
                    <div class="editor-panel-switch" aria-label="Panel del editor">
                        <button type="button" class="is-active" data-editor-panel-button="design">Diseño</button>
                        <button type="button" data-editor-panel-button="content">Contenido</button>
                        <button type="button" data-editor-panel-button="assets">Archivos</button>
                    </div>
                    <div class="easy-actions">
                        <button type="button" data-easy-action="repair">Reparar distribución</button>
                        <button type="button" data-easy-action="full-image">Usar imagen completa</button>
                    </div>
                    <div class="component-tools" data-component-tools>
                        <span>Componentes</span>
                        <button type="button" data-add-component="TEXTO">Texto</button>
                        <button type="button" data-add-component="IMAGEN">Imagen</button>
                        <button type="button" data-add-component="BOTON">Botón</button>
                    </div>
                    <p class="simple-editor-help">
                        Selecciona una sección, ajusta su diseño y agrega componentes sin salir del editor.
                    </p>
                `;
                panelHeading.insertAdjacentElement('afterend', toolbar);
            }
        }

        const propertyGroups = [...root.querySelectorAll('.properties-panel > .property-group')];
        propertyGroups.forEach((group, index) => {
            if (group.hasAttribute('data-universal-inspector') || group.hasAttribute('data-section-properties') || index <= 1) {
                group.dataset.editorGroup = 'design';
            } else if (group.classList.contains('quick-content-panel') || group.querySelector('[data-content-form], [data-guest-form]')) {
                group.dataset.editorGroup = 'content';
            } else if (group.querySelector('[data-asset-form], [data-asset-list]')) {
                group.dataset.editorGroup = 'assets';
            } else {
                group.dataset.editorGroup = 'content';
            }
        });

        const advancedSelectors = [
            '[data-custom-layer-name]',
            '[data-custom-layer-text]',
            '[data-custom-layer-fit]',
            '[data-layer-preset]',
            '[data-config-field="decorStyle"]',
            '[data-config-field="backgroundRepeat"]',
            '[data-config-field="backgroundBrightness"]',
            '[data-config-field="backgroundBlur"]',
            '[data-layer-action="duplicate"]',
            '[data-layer-action="delete"]',
        ];
        advancedSelectors.forEach((selector) => {
            root.querySelectorAll(selector).forEach((element) => {
                const wrapper = element.closest('label, .layer-actions') || element;
                wrapper.classList.add('advanced-only');
            });
        });

        root.querySelectorAll('[data-editor-mode]').forEach((button) => {
            button.addEventListener('click', () => setEditorMode(button.dataset.editorMode));
        });
        root.querySelectorAll('[data-editor-panel-button]').forEach((button) => {
            button.addEventListener('click', () => setEditorPanel(button.dataset.editorPanelButton));
        });
        root.querySelector('[data-editor-context-open]')?.addEventListener('click', (event) => {
            const panel = event.currentTarget.dataset.targetPanel || 'design';
            setEditorPanel(panel);
            root.querySelector(
                `[data-editor-group="${panel}"]:not([hidden])`
            )?.scrollIntoView({
                block: 'start',
                behavior: 'smooth',
            });
        });
        root.querySelector('[data-inspector-target]')?.addEventListener('change', () => {
            if (selectedComponent() && root.querySelector('[data-inspector-target]')?.value !== 'component') {
                selectedComponentId = null;
            }
            updateUniversalInspector();
            renderAll();
        });
        root.querySelectorAll('[data-inspector-panel]').forEach((button) => {
            button.addEventListener('click', () => setEditorPanel(button.dataset.inspectorPanel));
        });
        root.querySelectorAll('[data-inspector-field]').forEach((field) => {
            field.addEventListener('input', () => {
                const target = inspectorTargetType();
                const value = field.type === 'checkbox' ? field.checked : field.value;
                setInspectorValue(target, field.dataset.inspectorField, value);
                setState(target === 'component' ? 'Cambios sin guardar en componente' : 'Cambios sin guardar');
                renderAll();
            });
            field.addEventListener('change', () => {
                const component = selectedComponent();
                if (component) {
                    saveBuilderComponent(component, { skipRealRefresh: true }).catch((error) => setState(error.message));
                }
            });
        });
        root.querySelector('[data-inspector-action="delete-component"]')?.addEventListener('click', () => {
            const component = selectedComponent();
            if (!component) return;
            deleteBuilderComponent(component).catch((error) => setState(error.message));
        });
        root.querySelector('[data-component-tree]')?.addEventListener('dragstart', (event) => {
            const row = event.target.closest('.component-tree-row[draggable="true"]');
            if (!row || event.target.closest('[data-tree-tool]')) {
                event.preventDefault();
                return;
            }
            componentTreeDrag = treePayloadFromRow(row);
            if (!componentTreeDrag) {
                event.preventDefault();
                return;
            }
            row.classList.add('is-dragging');
            event.dataTransfer.effectAllowed = 'move';
            event.dataTransfer.setData('application/x-component-tree', JSON.stringify(componentTreeDrag));
            event.dataTransfer.setData('text/plain', JSON.stringify(componentTreeDrag));
        });
        root.querySelector('[data-component-tree]')?.addEventListener('dragover', (event) => {
            const row = event.target.closest('.component-tree-row[draggable="true"]');
            if (!row || !componentTreeDrag) return;
            const target = treePayloadFromRow(row);
            if (!compatibleTreeDrop(componentTreeDrag, target)) return;
            event.preventDefault();
            event.dataTransfer.dropEffect = 'move';
            root.querySelectorAll('.component-tree-row.is-drop-target').forEach((item) => item.classList.remove('is-drop-target'));
            row.classList.add('is-drop-target');
        });
        root.querySelector('[data-component-tree]')?.addEventListener('dragleave', (event) => {
            const row = event.target.closest('.component-tree-row');
            if (row && !row.contains(event.relatedTarget)) {
                row.classList.remove('is-drop-target');
            }
        });
        root.querySelector('[data-component-tree]')?.addEventListener('drop', (event) => {
            const row = event.target.closest('.component-tree-row[draggable="true"]');
            if (!row) return;
            const target = treePayloadFromRow(row);
            const source = componentTreeDrag || (() => {
                try {
                    return JSON.parse(event.dataTransfer.getData('application/x-component-tree') || event.dataTransfer.getData('text/plain') || 'null');
                } catch (error) {
                    return null;
                }
            })();
            if (!compatibleTreeDrop(source, target)) return;
            event.preventDefault();
            root.querySelectorAll('.component-tree-row.is-drop-target, .component-tree-row.is-dragging').forEach((item) => {
                item.classList.remove('is-drop-target', 'is-dragging');
            });
            componentTreeDrag = null;
            applyComponentTreeDrop(source, target);
        });
        root.querySelector('[data-component-tree]')?.addEventListener('dragend', () => {
            componentTreeDrag = null;
            root.querySelectorAll('.component-tree-row.is-drop-target, .component-tree-row.is-dragging').forEach((item) => {
                item.classList.remove('is-drop-target', 'is-dragging');
            });
        });
        root.querySelector('[data-component-tree]')?.addEventListener('click', (event) => {
            const tool = event.target.closest('[data-tree-tool]');
            if (tool) {
                const row = tool.closest('.component-tree-row');
                if (!row) return;
                event.stopPropagation();
                const sectionId = Number(row.dataset.treeSectionId || 0);
                if (sectionId) selectedId = sectionId;
                const section = selectedSection();
                const cfg = section ? ensureSectionConfig(section) : null;
                const layerId = row.dataset.treeLayerId || '';
                const componentId = Number(row.dataset.treeComponentId || 0);
                const component = componentId ? builderComponentById(componentId) : null;
                const action = tool.dataset.treeTool;

                if (component) {
                    selectedComponentId = component.id;
                    if (action === 'toggle-visible') component.hidden = !component.hidden;
                    if (action === 'toggle-lock') component.locked = !component.locked;
                    if (action === 'z-back') component.zIndex = clamp((Number(component.zIndex) || 20) - 1, 1, 100);
                    if (action === 'z-front') component.zIndex = clamp((Number(component.zIndex) || 20) + 1, 1, 100);
                    if (action === 'delete') {
                        deleteBuilderComponent(component).catch((error) => setState(error.message));
                        return;
                    }
                    saveBuilderComponent(component, { skipRealRefresh: action !== 'toggle-visible' }).catch((error) => setState(error.message));
                    renderAll();
                    return;
                }

                selectedComponentId = null;
                if (layerId && cfg) {
                    cfg.activeLayer = layerId;
                    if (action === 'toggle-visible') setLayerVisibility(cfg, layerId);
                    if (action === 'toggle-lock') setLayerLocked(cfg, layerId);
                    if (action === 'z-back') moveLayerFromList(cfg, layerId, -1);
                    if (action === 'z-front') moveLayerFromList(cfg, layerId, 1);
                    if (action === 'delete' && isCustomLayer(layerId)) {
                        cfg.activeLayer = layerId;
                        deleteActiveCustomLayer(cfg);
                    }
                    setState('Cambios sin guardar');
                    renderAll();
                    return;
                }

                if (section) {
                    if (action === 'toggle-visible') {
                        section.visible = !section.visible;
                        setState('Cambios sin guardar');
                        renderAll();
                    }
                }
                return;
            }
            const row = event.target.closest('[data-tree-action]');
            if (!row) return;
            const action = row.dataset.treeAction;
            const sectionId = Number(row.dataset.treeSectionId || 0);
            const inspectorSelect = root.querySelector('[data-inspector-target]');

            if (action === 'page') {
                selectedComponentId = null;
                if (inspectorSelect) inspectorSelect.value = 'section';
                renderAll();
                return;
            }

            if (sectionId) selectedId = sectionId;
            const section = selectedSection();
            const cfg = section ? ensureSectionConfig(section) : null;

            if (action === 'section') {
                selectedComponentId = null;
                if (inspectorSelect) inspectorSelect.value = 'section';
            } else if (action === 'layer' && cfg) {
                selectedComponentId = null;
                cfg.activeLayer = row.dataset.treeLayerId || 'background';
                if (inspectorSelect) inspectorSelect.value = 'layer';
            } else if (action === 'real') {
                selectedComponentId = null;
                if (inspectorSelect) inspectorSelect.value = 'real';
            } else if (action === 'component') {
                const componentId = Number(row.dataset.treeComponentId || 0);
                if (componentId) selectedComponentId = componentId;
                if (inspectorSelect) inspectorSelect.value = 'component';
            }

            setEditorPanel('design');
            renderAll();
        });
        root.querySelector('[data-easy-action="repair"]')?.addEventListener('click', () => applyEasyLayout());
        root.querySelector('[data-easy-action="full-image"]')?.addEventListener('click', () => applyEasyLayout({ fullImage: true }));
        root.querySelectorAll('[data-add-component]').forEach((button) => {
            button.addEventListener('click', () => {
                createBuilderComponent(button.dataset.addComponent).catch((error) => setState(error.message));
            });
        });

        root.addEventListener('input', (event) => {
            if (event.target.matches('input[type="range"]')) updateRangeReadouts();
        });

        setEditorMode('simple');
        setEditorPanel('design');
        updateRangeReadouts();

        const requiredControls = [
            '[data-editor-mode="simple"]',
            '[data-editor-mode="advanced"]',
            '[data-editor-panel-button="design"]',
            '[data-editor-panel-button="content"]',
            '[data-editor-panel-button="assets"]',
            '[data-easy-action="repair"]',
            '[data-easy-action="full-image"]',
            '[data-add-component="TEXTO"]',
            '[data-add-component="IMAGEN"]',
            '[data-add-component="BOTON"]',
        ];

        const missingControls = requiredControls.filter(
            (selector) => !root.querySelector(selector)
        );

        root.dataset.editorToolsReady =
            missingControls.length ? 'false' : 'true';

        if (missingControls.length) {
            console.warn(
                'DIRTEC Editor: herramientas faltantes:',
                missingControls
            );
            setState('Editor cargado con herramientas incompletas');
        }
    }

    function renderAll() {
        applyTheme();
        renderSectionList();
        renderComponentTree();
        renderPreview();
        fillProperties();
        updateEditorContextCard();
    }

    function moveSection(index, direction) {
        const ordered = sortedSections();
        const targetIndex = index + direction;
        if (targetIndex < 0 || targetIndex >= ordered.length) return;
        const current = ordered[index];
        const target = ordered[targetIndex];
        const currentOrder = current.order;
        current.order = target.order;
        target.order = currentOrder;
        selectedId = current.sectionId;
        setState('Cambios sin guardar');
        renderAll();
    }

    function reorderByDrop(draggedId, targetId) {
        if (!draggedId || !targetId || draggedId === targetId) return;
        const ordered = sortedSections();
        const from = ordered.findIndex((section) => section.sectionId === draggedId);
        const to = ordered.findIndex((section) => section.sectionId === targetId);
        if (from < 0 || to < 0) return;
        const [dragged] = ordered.splice(from, 1);
        ordered.splice(to, 0, dragged);
        ordered.forEach((section, index) => {
            section.order = (index + 1) * 10;
        });
        selectedId = draggedId;
        setState('Cambios sin guardar');
        renderAll();
    }

    function escapeHtml(value) {
        return String(value || '').replace(/[&<>"']/g, (char) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        }[char]));
    }

    function eventData() {
        return content.event || {};
    }

    function formatDateTime(value) {
        if (!value) return 'Fecha por confirmar';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString('es-MX', {
            day: '2-digit',
            month: 'long',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    function previewList(items, emptyText, mapper, limit = 4) {
        const visible = (items || []).filter((item) => item.visible !== false).slice(0, limit);
        if (!visible.length) return `<p class="muted">${escapeHtml(emptyText)}</p>`;
        return `<div class="preview-mini-list">${visible.map(mapper).join('')}</div>`;
    }

    function namesPreview() {
        const event = eventData();
        const main = event.mainName || 'Nombre principal';
        const secondary = event.showSecondaryName === false ? '' : (event.secondaryName || 'Nombre secundario');
        return secondary
            ? `<strong class="preview-script">${escapeHtml(main)} & ${escapeHtml(secondary)}</strong>`
            : `<strong class="preview-script">${escapeHtml(main)}</strong>`;
    }

    function peopleBySection(section) {
        return (content.people || []).filter((item) => item.visible !== false && item.section === section);
    }

    function previewGuestSummary() {
        const first = (guests.groups || [])[0];
        if (!first) return '<p class="muted">Sin invitado de prueba capturado.</p>';
        return `
            <div class="summary-grid">
                <div class="info-box">
                    <div class="label">Invitacion para</div>
                    <div class="value guest-summary-name">${escapeHtml(first.type === 'FAMILIAR' ? `Familia ${first.name}` : first.name)}</div>
                </div>
                <div class="info-box">
                    <div class="label">Tipo</div>
                    <div class="value">${escapeHtml(first.typeLabel || first.type || 'Invitado')}</div>
                </div>
                <div class="info-box">
                    <div class="label">Lugares</div>
                    <div class="value">${escapeHtml(first.places || 0)}</div>
                </div>
            </div>
        `;
    }

    function extractMapPreviewUrl(embedHtml, fallbackUrl) {
        const source = String(embedHtml || '').trim();

        if (source) {
            const srcMatch = source.match(/\bsrc\s*=\s*["']([^"']+)["']/i);
            if (srcMatch?.[1]) return srcMatch[1];
        }

        return String(fallbackUrl || '').trim();
    }

    function formatDatePart(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return String(value);
        return new Intl.DateTimeFormat('es-MX', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
        }).format(date);
    }

    function formatTimePart(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return '';
        return new Intl.DateTimeFormat('es-MX', {
            hour: '2-digit',
            minute: '2-digit',
        }).format(date);
    }

    function detailLocationPreviewHtml({
        kind,
        title,
        date,
        place,
        address,
        mapUrl,
        mapEmbed,
        mediaAsset = {},
        itemConfig = {},
    }) {
        const previewUrl = extractMapPreviewUrl(mapEmbed, mapUrl);
        const safeMapUrl = mapUrl ? escapeHtml(mapUrl) : (previewUrl ? escapeHtml(previewUrl) : '');
        const mediaUrl = mediaAsset?.url || '';
        const showMedia = itemConfig.showMedia !== false && itemConfig.mediaPosition !== 'hidden' && Boolean(mediaUrl);
        const mapAsset = itemConfig.mapAsset && typeof itemConfig.mapAsset === 'object' ? itemConfig.mapAsset : {};
        const mapDisplay = itemConfig.mapDisplay || 'button-map';
        const mapsAllowed = itemConfig.showMaps !== false && mapDisplay !== 'hidden';
        const showTitle = itemConfig.showTitle !== false;
        const showDate = itemConfig.showDate !== false;
        const showTime = itemConfig.showTime !== false;
        const showPlace = itemConfig.showPlace !== false;
        const showAddress = itemConfig.showAddress !== false;
        const showButton =
            itemConfig.showButton !== false &&
            ['button-map', 'button-only'].includes(mapDisplay);
        const showMap = mapsAllowed && ['button-map', 'map-only'].includes(mapDisplay);
        const hasButton = Boolean(safeMapUrl);
        const buttonLabel = itemConfig.buttonLabel || 'Ver ubicacion';
        const dateText = formatDatePart(date);
        const timeText = formatTimePart(date);

        return `
            <article
                class="info-box event-place-card"
                data-detail-kind="${escapeHtml(kind)}"
                data-real-card-media-position="${escapeHtml(itemConfig.mediaPosition || 'top')}"
                style="--real-card-bg:${escapeHtml(itemConfig.cardBg || '#ffffff')};order:${Number(itemConfig.order || 0)};"
            >
                ${showMedia ? `
                    <div class="place-media">
                        ${mediaAsset.isVideo
                            ? `<video src="${escapeHtml(mediaUrl)}" muted playsinline preload="metadata"></video>`
                            : `<img src="${escapeHtml(mediaUrl)}" alt="${escapeHtml(title)}">`
                        }
                    </div>
                ` : ''}
                ${showTitle ? `<div class="card-title">${escapeHtml(title)}</div>` : ''}
                ${showDate && dateText ? `<div class="value">${escapeHtml(dateText)}</div>` : ''}
                ${showTime && timeText ? `<p class="place-time">${escapeHtml(timeText)}</p>` : ''}
                ${showPlace ? `<p class="place-name">${escapeHtml(place || 'Lugar por confirmar')}</p>` : ''}
                ${showAddress && address ? `<p class="place-address">${escapeHtml(address)}</p>` : ''}
                ${showButton ? `
                ${
                    hasButton
                        ? `
                            <a
                                class="btn secondary"
                                href="${safeMapUrl}"
                                target="_blank"
                                rel="noopener"
                                tabindex="-1"
                                aria-disabled="true"
                            >
                                ${escapeHtml(buttonLabel)}
                            </a>
                        `
                        : `
                            <span class="btn secondary is-disabled">
                                ${escapeHtml(buttonLabel)}
                            </span>
                        `
                }
                ` : ''}
                ${showMap ? `
                <div class="map-card preview-map-placeholder">
                    ${mapAsset.url
                        ? (mapAsset.isVideo
                            ? `<video src="${escapeHtml(mapAsset.url)}" muted playsinline preload="metadata"></video>`
                            : `<img src="${escapeHtml(mapAsset.url)}" alt="Imagen de ubicacion">`
                        )
                        : `<small>${previewUrl ? 'Mapa configurado' : 'Mapa pendiente'}</small>`
                    }
                </div>
                ` : ''}
            </article>
        `;
    }

    function giftPreviewHtml(item) {
        const isDeposit = item.isDeposit || item.bank || item.holder || item.account || item.clabe;
        if (isDeposit) {
            return `
                <div class="gift-box deposit-box">
                    <span class="gift-kind">Deposito</span>
                    <strong>${escapeHtml(item.name || 'Datos bancarios')}</strong>
                    ${item.bank ? `<p><b>Banco:</b> ${escapeHtml(item.bank)}</p>` : ''}
                    ${item.holder ? `<p><b>Titular:</b> ${escapeHtml(item.holder)}</p>` : ''}
                    ${item.account ? `<p><b>Cuenta:</b> ${escapeHtml(item.account)}</p>` : ''}
                    ${item.clabe ? `<p><b>CLABE:</b> ${escapeHtml(item.clabe)}</p>` : ''}
                    ${item.instructions ? `<small>${escapeHtml(item.instructions)}</small>` : ''}
                </div>
            `;
        }
        return `
            <div class="gift-box">
                <span class="gift-kind">${escapeHtml(item.url ? 'Tienda' : 'Regalo')}</span>
                <strong>${escapeHtml(item.name || item.typeLabel || 'Regalo')}</strong>
                ${item.url ? `<p>${escapeHtml(item.url)}</p>` : `<p>${escapeHtml(item.instructions || 'Informacion pendiente de completar.')}</p>`}
            </div>
        `;
    }

    function albumPreviewHtml() {
        const assets = (config.theme?.albumAssets || []).filter((asset) => asset?.url).slice(0, 6);
        if (!assets.length) {
            return '<p class="section-copy muted">Agrega fotos al album para verlas aqui.</p>';
        }
        return `
            <div class="album-grid">
                ${assets.map((asset) => `
                    <figure>
                        ${asset.isVideo
                            ? `<video src="${escapeHtml(asset.url)}" playsinline muted preload="metadata"></video>`
                            : `<img src="${escapeHtml(asset.url)}" alt="${escapeHtml(asset.title || 'Foto del evento')}">`
                        }
                        ${asset.title ? `<figcaption>${escapeHtml(asset.title)}</figcaption>` : ''}
                    </figure>
                `).join('')}
            </div>
        `;
    }

    function sectionPreviewHtml(section, cfg = ensureSectionConfig(section)) {
        const event = eventData();
        const description = section.description ? `<p>${escapeHtml(section.description)}</p>` : '';
        if (section.type === 'PORTADA') {
            return `
                <div class="preview-cover-copy">
                    <span>${escapeHtml(event.coverPhrase || section.title || 'Tu invitacion')}</span>
                    ${namesPreview()}
                    <small>${escapeHtml(formatDateTime(event.receptionDate || event.ceremonyDate))}</small>
                </div>
            `;
        }
        if (section.type === 'PADRES_PADRINOS') {
            const novia = peopleBySection('PADRES_NOVIA');
            const novio = peopleBySection('PADRES_NOVIO');
            const padrinos = peopleBySection('PADRINOS');
            return `
                <div class="preview-parent-grid">
                    <div><strong>Padres de ${escapeHtml((event.mainLabel || 'novia').toLowerCase())}</strong>${previewList(novia, 'Pendiente', (item) => `<p>${escapeHtml(item.name)}</p>`, 3)}</div>
                    <div><strong>Padres de ${escapeHtml((event.secondaryLabel || 'novio').toLowerCase())}</strong>${previewList(novio, 'Pendiente', (item) => `<p>${escapeHtml(item.name)}</p>`, 3)}</div>
                </div>
                <div class="preview-sponsors"><strong>Padrinos</strong>${previewList(padrinos, 'Sin padrinos capturados', (item) => `<p>${escapeHtml(item.name)}</p>`, 4)}</div>
            `;
        }
        if (section.type === 'CUENTA_REGRESIVA') {
            return `
                <div class="preview-countdown">
                    <div>
                        <span>115<small>Días</small></span>
                        <span>14<small>Horas</small></span>
                        <span>52<small>Minutos</small></span>
                        <span>26<small>Segundos</small></span>
                    </div>
                </div>
            `;
        }
        if (section.type === 'DETALLES') {
            const real = normalizeRealContentConfig(cfg.realContent, section.type);
            const ceremony = real.items.ceremony;
            const reception = real.items.reception;
            return `
                <div class="preview-detail-flow">
                    ${description}
                    <div class="event-detail-grid">
                        ${ceremony.visible !== false ? detailLocationPreviewHtml({
                            kind: 'ceremony',
                            title: ceremony.label || 'Ceremonia',
                            date: event.ceremonyDate,
                            place: event.ceremonyPlace || 'Templo por confirmar',
                            address: real.showAddress && ceremony.showAddress !== false ? event.ceremonyAddress : '',
                            mapUrl: real.showMaps && ceremony.showMaps !== false ? event.ceremonyMapUrl : '',
                            mapEmbed: real.showMaps && ceremony.showMaps !== false ? event.ceremonyMapEmbed : '',
                            mediaAsset: config.theme?.ceremonyAsset?.url
                                ? config.theme.ceremonyAsset
                                : { url: event.ceremonyMediaUrl || '', isVideo: Boolean(event.ceremonyMediaIsVideo), title: ceremony.label || 'Ceremonia' },
                            itemConfig: ceremony,
                        }) : ''}
                        ${reception.visible !== false ? detailLocationPreviewHtml({
                            kind: 'reception',
                            title: reception.label || 'Recepcion',
                            date: event.receptionDate,
                            place: event.receptionPlace || 'Salon por confirmar',
                            address: real.showAddress && reception.showAddress !== false ? event.receptionAddress : '',
                            mapUrl: real.showMaps && reception.showMaps !== false ? event.receptionMapUrl : '',
                            mapEmbed: real.showMaps && reception.showMaps !== false ? event.receptionMapEmbed : '',
                            mediaAsset: config.theme?.receptionAsset?.url
                                ? config.theme.receptionAsset
                                : { url: event.receptionMediaUrl || '', isVideo: Boolean(event.receptionMediaIsVideo), title: reception.label || 'Recepcion' },
                            itemConfig: reception,
                        }) : ''}
                    </div>
                </div>
            `;
        }
        if (section.type === 'DRESS_CODE') {
            return `<div class="preview-dress"><strong>${escapeHtml(event.dressCode || 'Dress code')}</strong><p>${escapeHtml(event.dressCodeText || 'Indicaciones por capturar.')}</p></div>`;
        }
        if (section.type === 'ITINERARIO') {
            return previewList(content.itinerary, 'Sin itinerario capturado', (item) => `<div><strong>${escapeHtml(item.time || '')}</strong><span>${escapeHtml(item.title || '')}</span></div>`, 5);
        }
        if (section.type === 'REGALOS') {
            const gifts = (content.gifts || []).filter((item) => item.visible !== false).slice(0, 6);
            return `
                <div class="gift-grid">
                    ${gifts.length ? gifts.map(giftPreviewHtml).join('') : '<p class="section-copy muted">Aun no se han agregado opciones de regalo.</p>'}
                </div>
            `;
        }
        if (section.type === 'ALBUM') {
            return albumPreviewHtml();
        }
        if (section.type === 'ALBUM_COMPARTIDO') {
            return `
                <div class="shared-album-content">
                    <p class="shared-album-message">${escapeHtml(event.sharedAlbumText || section.description || 'Comparte con nosotros las fotos y videos que captures durante el evento.')}</p>
                    <div class="btn-row">
                        <a class="btn" href="${escapeHtml(event.sharedAlbumUrl || '#')}" target="_blank" rel="noopener" tabindex="-1" aria-disabled="true">
                            Subir fotos y videos
                        </a>
                    </div>
                </div>
            `;
        }
        if (section.type === 'RSVP') {
            return `
                <div class="invitation-summary">
                    <h2 class="section-title">${escapeHtml(event.invitationTitle || section.title || 'Confirmar asistencia')}</h2>
                    <p class="section-copy">${escapeHtml(event.invitationText || event.rsvpText || 'Confirma tu asistencia.')}</p>
                    ${previewGuestSummary()}
                </div>
                <div class="rsvp-form preview-rsvp-form">
                    <div class="guest-box">
                        <div class="guest-head">
                            <h3 class="guest-name">Invitado de prueba</h3>
                            <span class="pill">Formulario RSVP</span>
                        </div>
                        <div class="radio-row">
                            <div class="option"><span class="preview-radio"></span><label>Si asistire</label></div>
                            <div class="option"><span class="preview-radio"></span><label>No asistire</label></div>
                        </div>
                    </div>
                </div>
            `;
        }
        return description || '<p class="muted">Seccion lista para personalizar.</p>';
    }

    function fillContentForm() {
        const form = root.querySelector('[data-content-form]');
        if (!form || !content.event) return;
        Object.entries(content.event).forEach(([key, value]) => {
            const field = form.elements[key];
            if (!field) return;
            if (field.type === 'checkbox') {
                field.checked = Boolean(value);
            } else {
                field.value = value ?? '';
            }
        });
    }

    function formToObject(form) {
        const data = {};
        Array.from(form.elements).forEach((field) => {
            if (!field.name) return;
            data[field.name] = field.type === 'checkbox' ? field.checked : field.value;
        });
        return data;
    }

    function collectionLabel(collection, item) {
        if (collection === 'people') return `${item.sectionLabel || item.section} · ${item.label || ''}`;
        if (collection === 'gifts') return `${item.typeLabel || item.type}${item.visible ? '' : ' · Oculto'}`;
        if (collection === 'itinerary') return `${item.time || ''}${item.visible ? '' : ' · Oculto'}`;
        return '';
    }

    function itemTitle(collection, item) {
        if (collection === 'people') return item.name;
        if (collection === 'gifts') return item.name;
        if (collection === 'itinerary') return item.title;
        return 'Item';
    }

    function fillCollectionForm(collection, item) {
        const form = root.querySelector(`[data-collection-form="${collection}"]`);
        if (!form) return;
        form.reset();
        Object.entries(item).forEach(([key, value]) => {
            const field = form.elements[key];
            if (!field) return;
            if (field.type === 'checkbox') {
                field.checked = Boolean(value);
            } else {
                field.value = value ?? '';
            }
        });
    }

    function renderCollection(collection) {
        const list = root.querySelector(`[data-collection-list="${collection}"]`);
        if (!list) return;
        const items = content[collection] || [];
        list.innerHTML = '';
        if (!items.length) {
            list.innerHTML = '<p class="muted">Sin registros todavia.</p>';
            return;
        }
        items.forEach((item) => {
            const article = document.createElement('article');
            article.className = 'quick-item';
            article.innerHTML = `
                <div>
                    <strong>${escapeHtml(itemTitle(collection, item))}</strong>
                    <span>${escapeHtml(collectionLabel(collection, item))}</span>
                </div>
                <div class="quick-item-actions">
                    <button type="button" data-edit-item>Editar</button>
                    <button type="button" data-delete-item>Eliminar</button>
                </div>
            `;
            article.querySelector('[data-edit-item]').addEventListener('click', () => fillCollectionForm(collection, item));
            article.querySelector('[data-delete-item]').addEventListener('click', () => {
                saveCollectionItem(collection, { id: item.id, action: 'delete' }).catch((error) => setState(error.message));
            });
            list.appendChild(article);
        });
    }

    function renderContent() {
        fillContentForm();
        ['people', 'gifts', 'itinerary'].forEach(renderCollection);
    }

    function renderVersions() {
        if (!versionList) return;
        versionList.innerHTML = '';
        if (!versions.length) {
            versionList.innerHTML = '<p class="muted">Guarda o publica para crear historial.</p>';
            return;
        }
        versions.forEach((version) => {
            const article = document.createElement('article');
            article.className = 'version-item';
            article.innerHTML = `
                <div>
                    <strong>${escapeHtml(version.name)}</strong>
                    <span>${escapeHtml(version.createdAt || '')}${version.published ? ' · Publicada' : ' · Borrador'}</span>
                </div>
                <button type="button" data-restore-version>Restaurar</button>
            `;
            const swatch = document.createElement('span');
            swatch.className = 'version-swatch';
            swatch.style.background = `linear-gradient(135deg, ${version.primary || '#22252d'}, ${version.accent || '#c8a96a'})`;
            article.prepend(swatch);
            const meta = article.querySelector('span:not(.version-swatch)');
            if (meta) {
                meta.textContent = `${version.createdAt || ''} - ${version.published ? 'Publicada' : 'Borrador'} - ${Number(version.sectionCount || 0)} secciones`;
            }
            const note = document.createElement('small');
            note.textContent = version.firstTitle || 'Sin titulo visible';
            article.querySelector('div')?.appendChild(note);
            article.querySelector('[data-restore-version]').addEventListener('click', () => {
                restoreVersion(version.id).catch((error) => setState(error.message));
            });
            versionList.appendChild(article);
        });
    }

    function fillTableSelects() {
        root.querySelectorAll('[data-table-select]').forEach((select) => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">Sin mesa</option>';
            (guests.tables || []).forEach((table) => {
                const option = document.createElement('option');
                option.value = table.id;
                option.textContent = `${table.name} (${table.occupied}/${table.capacity})`;
                select.appendChild(option);
            });
            select.value = currentValue;
        });
    }

    function fillGuestGroupForm(group = {}) {
        const form = root.querySelector('[data-guest-group-form]');
        if (!form) return;
        form.reset();
        Object.entries(group).forEach(([key, value]) => {
            const field = form.elements[key];
            if (!field) return;
            field.value = value ?? '';
        });
        form.elements.familyGuests.value = '';
    }

    function fillGuestPersonForm(groupId, guest = {}) {
        const form = root.querySelector('[data-guest-person-form]');
        if (!form) return;
        form.reset();
        form.elements.groupId.value = groupId || '';
        Object.entries(guest).forEach(([key, value]) => {
            const field = form.elements[key];
            if (!field) return;
            if (field.type === 'checkbox') {
                field.checked = Boolean(value);
            } else {
                field.value = value ?? '';
            }
        });
    }

    function renderGuests() {
        fillTableSelects();
        if (!guestList) return;
        const groups = guests.groups || [];
        guestList.innerHTML = '';
        if (!groups.length) {
            guestList.innerHTML = '<p class="muted">Aun no hay invitados capturados.</p>';
            return;
        }
        groups.forEach((group) => {
            const article = document.createElement('article');
            article.className = 'guest-editor-card';
            article.innerHTML = `
                <div class="guest-editor-head">
                    <div>
                        <strong>${escapeHtml(group.type === 'FAMILIAR' ? `Familia ${group.name}` : group.name)}</strong>
                        <span>${escapeHtml(group.typeLabel)} · ${group.places} lugar(es) · Mesa ${escapeHtml(group.tableName || 'sin asignar')}</span>
                    </div>
                    <img src="${group.qrUrl}" alt="QR invitacion">
                </div>
                <div class="guest-link-row">
                    <input readonly value="${escapeHtml(group.link)}">
                    <button type="button" data-copy-link>Copiar</button>
                </div>
                <div class="quick-item-actions">
                    <button type="button" data-edit-group>Editar grupo</button>
                    <button type="button" data-delete-group>Eliminar grupo</button>
                </div>
                ${(group.guests || []).length || group.type === 'FAMILIAR' || group.type === 'PERSONAL' ? '<div class="family-guest-list"></div><button class="mini-action" type="button" data-new-family-guest>Agregar persona / acompanante</button>' : ''}
            `;
            article.querySelector('[data-copy-link]')?.addEventListener('click', () => {
                navigator.clipboard?.writeText(group.link);
                setState('Link copiado');
            });
            article.querySelector('[data-edit-group]')?.addEventListener('click', () => fillGuestGroupForm(group));
            article.querySelector('[data-delete-group]')?.addEventListener('click', () => {
                saveGuestGroup({ id: group.id, action: 'delete' }).catch((error) => setState(error.message));
            });
            article.querySelector('[data-new-family-guest]')?.addEventListener('click', () => fillGuestPersonForm(group.id));
            const familyList = article.querySelector('.family-guest-list');
            if (familyList) {
                (group.guests || []).forEach((guest) => {
                    const guestItem = document.createElement('div');
                    guestItem.className = 'family-guest-item';
                    guestItem.innerHTML = `
                        <div>
                            <strong>${escapeHtml(`${guest.name}${guest.lastName ? ` ${guest.lastName}` : ''}`)}</strong>
                            <span>${escapeHtml(guest.type)} · Mesa ${escapeHtml(guest.tableName || 'sin asignar')}</span>
                        </div>
                        <div class="quick-item-actions">
                            <button type="button" data-edit-family-guest>Editar</button>
                            <button type="button" data-delete-family-guest>Eliminar</button>
                        </div>
                    `;
                    guestItem.querySelector('[data-edit-family-guest]').addEventListener('click', () => fillGuestPersonForm(group.id, guest));
                    guestItem.querySelector('[data-delete-family-guest]').addEventListener('click', () => {
                        saveGuestPerson({ id: guest.id, groupId: group.id, action: 'delete' }).catch((error) => setState(error.message));
                    });
                    familyList.appendChild(guestItem);
                });
            }
            guestList.appendChild(article);
        });
    }

    async function saveGuestGroup(payload) {
        setState('Guardando invitados...');
        const response = await fetch(root.dataset.saveGuestGroupUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar grupo.');
        guests = data.guests || guests;
        setState(payload.action === 'delete' ? 'Grupo eliminado' : 'Grupo guardado');
        renderGuests();
        renderAll();
        refreshRealPreview();
    }

    async function saveGuestPerson(payload) {
        setState('Guardando invitado...');
        const response = await fetch(root.dataset.saveGuestUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar invitado.');
        guests = data.guests || guests;
        setState(payload.action === 'delete' ? 'Invitado eliminado' : 'Invitado guardado');
        renderGuests();
        renderAll();
        refreshRealPreview();
    }

    async function importGuests(form) {
        const formData = new FormData(form);
        setState('Importando lista...');
        const response = await fetch(root.dataset.importGuestsUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken() },
            body: formData,
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo importar la lista.');
        guests = data.guests || guests;
        setState(data.message || 'Lista importada');
        renderGuests();
        renderAll();
        refreshRealPreview();
    }

    async function saveContent(payload) {
        setState('Guardando contenido...');
        const response = await fetch(root.dataset.saveContentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar contenido.');
        content = data.content || content;
        setState('Contenido guardado');
        renderContent();
        renderAll();
        refreshRealPreview();
    }

    async function saveCollectionItem(collection, payload) {
        setState('Guardando registro...');
        const response = await fetch(root.dataset.saveContentItemUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify({ ...payload, collection }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar registro.');
        content = data.content || content;
        setState(payload.action === 'delete' ? 'Registro eliminado' : 'Registro guardado');
        renderContent();
        renderAll();
        refreshRealPreview();
    }

    async function restoreVersion(versionId) {
        setState('Restaurando version...');
        const response = await fetch(root.dataset.restoreVersionUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify({ versionId }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo restaurar.');
        config = data.config || config;
        versions = data.versions || versions;
        selectedId = config.sections?.[0]?.sectionId || selectedId;
        setState('Version restaurada en borrador');
        renderAll();
        renderVersions();
        refreshRealPreview();
    }

    async function applyTemplate() {
        const picker = root.querySelector('[data-template-picker]');
        const template = picker?.value;
        if (!template) {
            setState('Selecciona una plantilla.');
            return;
        }
        setState('Aplicando plantilla...');
        const response = await fetch(root.dataset.applyTemplateUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify({ template }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || 'No se pudo aplicar plantilla.');
        config = data.config || config;
        content = data.content || content;
        versions = data.versions || versions;
        selectedId = config.sections?.[0]?.sectionId || selectedId;
        setState('Plantilla aplicada al borrador');
        renderAll();
        renderContent();
        renderVersions();
        refreshRealPreview();
    }

    root.querySelectorAll('[data-theme-field]').forEach((field) => {
        field.addEventListener('input', () => {
            config.theme = config.theme || {};
            config.theme[field.dataset.themeField] = field.value;
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelectorAll('[data-section-field]').forEach((field) => {
        field.addEventListener('input', () => {
            const section = selectedSection();
            if (!section) return;
            const key = field.dataset.sectionField;
            section[key] = field.type === 'checkbox' ? field.checked : field.value;
            if (key === 'order') section[key] = Number(field.value || 0);
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelectorAll('[data-config-field]').forEach((field) => {
        field.addEventListener('input', () => {
            const section = selectedSection();
            if (!section) return;
            section.config = ensureSectionConfig(section);
            const key = field.dataset.configField;
            if (['backgroundX', 'backgroundY', 'backgroundScale'].includes(key)) {
                setBackgroundValue(section.config, key, field.value);
            } else {
                section.config[key] = field.type === 'checkbox' ? field.checked : field.value;
            }
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelectorAll('[data-real-content-field]').forEach((field) => {
        field.addEventListener('input', () => {
            const section = selectedSection();
            if (!section || !realContentSections.has(section.type)) return;
            const real = ensureSectionConfig(section).realContent;
            const key = field.dataset.realContentField;
            if (!key) return;
            if (field.type === 'checkbox') {
                real[key] = field.checked;
            } else if (field.type === 'range' || field.type === 'number') {
                const numeric = Number(field.value);
                real[key] = Number.isFinite(numeric) ? numeric : field.value;
            } else {
                real[key] = field.value;
            }
            section.config.realContent = normalizeRealContentConfig(real, section.type);
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelectorAll('[data-real-content-item]').forEach((field) => {
        field.addEventListener('input', () => {
            const section = selectedSection();
            if (!section || !realContentSections.has(section.type)) return;
            const real = ensureSectionConfig(section).realContent;
            const itemKey = field.dataset.realContentItem;
            const itemField = field.dataset.realContentItemField;
            if (!itemKey || !itemField) return;
            real.items = real.items || {};
            real.items[itemKey] = real.items[itemKey] || {};
            if (field.type === 'checkbox') {
                real.items[itemKey][itemField] = field.checked;
            } else if (field.type === 'number' || field.type === 'range') {
                const numeric = Number(field.value);
                real.items[itemKey][itemField] = Number.isFinite(numeric) ? numeric : field.value;
            } else {
                real.items[itemKey][itemField] = field.value;
            }
            section.config.realContent = normalizeRealContentConfig(real, section.type);
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelectorAll('[data-layer-select]').forEach((button) => {
        button.addEventListener('click', () => {
            const section = selectedSection();
            if (!section) return;
            ensureSectionConfig(section).activeLayer = button.dataset.layerSelect;
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    root.querySelector('[data-custom-layer-list]')?.addEventListener('click', (event) => {
        const button = event.target.closest('[data-layer-list-action]');
        if (!button) return;
        const section = selectedSection();
        if (!section) return;
        const cfg = ensureSectionConfig(section);
        const layerId = button.dataset.layerId;
        if (button.dataset.layerListAction === 'select') {
            cfg.activeLayer = layerId;
        }
        if (button.dataset.layerListAction === 'toggle') {
            setLayerVisibility(cfg, layerId);
        }
        if (button.dataset.layerListAction === 'lock') {
            setLayerLocked(cfg, layerId);
        }
        if (button.dataset.layerListAction === 'front') {
            moveLayerFromList(cfg, layerId, 1);
        }
        if (button.dataset.layerListAction === 'back') {
            moveLayerFromList(cfg, layerId, -1);
        }
        setState('Capa actualizada');
        renderAll();
    });

    root.querySelectorAll('[data-layer-field]').forEach((field) => {
        field.addEventListener('input', () => {
            const section = selectedSection();
            if (!section) return;
            const cfg = ensureSectionConfig(section);
            const layer = cfg.activeLayer || 'title';
            const key = field.dataset.layerField;
            const custom = customLayerByActive(cfg);
            if (custom) {
                setCustomLayerValue(custom, key, field.type === 'checkbox' ? field.checked : field.value);
            } else {
                setLayerValue(cfg, layer, key, field.type === 'checkbox' ? field.checked : field.value);
            }
            setState('Cambios sin guardar');
            renderAll();
        });
    });

    function setSelectedComponentField(field) {
        const component = selectedComponent();
        if (!component) return null;
        const key = field.dataset.componentField;
        if (!key) return component;
        if (field.type === 'checkbox') {
            component[key] = field.checked;
        } else {
            const numeric = Number(field.value);
            component[key] = Number.isFinite(numeric) ? numeric : field.value;
        }
        return component;
    }

    function setSelectedComponentProperty(field) {
        const component = selectedComponent();
        if (!component) return null;
        const key = field.dataset.componentProperty;
        if (!key) return component;
        component.properties = component.properties || {};
        if (field.type === 'number') {
            const numeric = Number(field.value);
            component.properties[key] = Number.isFinite(numeric) ? numeric : field.value;
        } else {
            component.properties[key] = field.value;
        }
        return component;
    }

    root.querySelectorAll('[data-component-field]').forEach((field) => {
        field.addEventListener('input', () => {
            const component = setSelectedComponentField(field);
            if (!component) return;
            setState('Cambios sin guardar en componente');
            if (field.dataset.componentField === 'hidden') {
                renderAll();
            } else {
                updateComponentPreview(component);
            }
        });
        field.addEventListener('change', () => {
            const component = selectedComponent();
            if (!component) return;
            saveBuilderComponent(component, {
                skipRealRefresh: field.dataset.componentField !== 'hidden',
            }).catch((error) => setState(error.message));
        });
    });

    root.querySelectorAll('[data-component-property]').forEach((field) => {
        field.addEventListener('input', () => {
            const component = setSelectedComponentProperty(field);
            if (!component) return;
            setState('Cambios sin guardar en componente');
            updateComponentPreview(component);
        });
        field.addEventListener('change', () => {
            const component = selectedComponent();
            if (!component) return;
            saveBuilderComponent(component, { skipRealRefresh: true }).catch((error) => setState(error.message));
        });
    });

    root.querySelectorAll('[data-component-action]').forEach((button) => {
        button.addEventListener('click', () => {
            const component = selectedComponent();
            if (!component) return;
            if (button.dataset.componentAction === 'delete') {
                deleteBuilderComponent(component).catch((error) => setState(error.message));
            }
        });
    });

    root.querySelector('[data-add-text-layer]')?.addEventListener('click', () => {
        const section = selectedSection();
        if (!section) return;
        addCustomLayer(section, {
            kind: 'text',
            name: 'Texto libre',
            text: 'Nuevo texto',
            x: 50,
            y: 50,
            width: 60,
            z: 4,
        });
    });

    root.querySelector('[data-custom-layer-name]')?.addEventListener('input', (event) => {
        const section = selectedSection();
        if (!section) return;
        const custom = customLayerByActive(ensureSectionConfig(section));
        if (!custom) return;
        custom.name = event.currentTarget.value.slice(0, 80);
        setState('Cambios sin guardar');
        renderAll();
    });

    root.querySelector('[data-custom-layer-text]')?.addEventListener('input', (event) => {
        const section = selectedSection();
        if (!section) return;
        const custom = customLayerByActive(ensureSectionConfig(section));
        if (!custom || custom.kind !== 'text') return;
        custom.text = event.currentTarget.value.slice(0, 220);
        setState('Cambios sin guardar');
        renderAll();
    });

    root.querySelector('[data-custom-layer-fit]')?.addEventListener('change', (event) => {
        const section = selectedSection();
        if (!section) return;
        const custom = customLayerByActive(ensureSectionConfig(section));
        if (!custom || custom.kind === 'text') return;
        custom.fit = event.currentTarget.value;
        setState('Cambios sin guardar');
        renderAll();
    });

    root.querySelector('[data-layer-preset]')?.addEventListener('change', (event) => {
        const section = selectedSection();
        if (!section || !event.currentTarget.value) return;
        const cfg = ensureSectionConfig(section);
        const layer = cfg.activeLayer || 'title';
        if (layer === 'background') return;
        applyLayerPreset(cfg, layer, event.currentTarget.value);
        setState('Preset aplicado');
        renderAll();
    });

    root.querySelectorAll('[data-layer-action]').forEach((button) => {
        button.addEventListener('click', () => {
            const section = selectedSection();
            if (!section) return;
            const cfg = ensureSectionConfig(section);
            const layer = cfg.activeLayer || 'title';
            if (layer === 'background') return;
            if (button.dataset.layerAction === 'front') moveLayerZ(cfg, layer, 1);
            if (button.dataset.layerAction === 'back') moveLayerZ(cfg, layer, -1);
            if (button.dataset.layerAction === 'reset') resetLayer(cfg, layer);
            if (button.dataset.layerAction === 'duplicate') duplicateActiveCustomLayer(cfg);
            if (button.dataset.layerAction === 'delete') deleteActiveCustomLayer(cfg);
            setState('Capa actualizada');
            renderAll();
        });
    });

    root.querySelector('[data-reset-image-controls]')?.addEventListener('click', () => {
        const section = selectedSection();
        if (!section) return;
        Object.assign(ensureSectionConfig(section), {
            backgroundFit: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundX: 50,
            backgroundY: 50,
            backgroundScale: 1,
            backgroundXMobile: 50,
            backgroundYMobile: 50,
            backgroundScaleMobile: 1,
            backgroundXTablet: 50,
            backgroundYTablet: 50,
            backgroundScaleTablet: 1,
            backgroundXDesktop: 50,
            backgroundYDesktop: 50,
            backgroundScaleDesktop: 1,
            backgroundOpacity: 1,
            backgroundBrightness: 1,
            backgroundBlur: 0,
            sectionHeight: 420,
        });
        setState('Imagen reajustada');
        renderAll();
    });

    async function syncQuickContentBeforeDesignPost() {
        const form = root.querySelector('[data-content-form]');
        if (!form) return;
        await saveContent(formToObject(form));
    }

    async function postJson(url, { syncContent = false } = {}) {
        if (syncContent) {
            await syncQuickContentBeforeDesignPost();
        }
        setState('Guardando...');
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify(config),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            throw new Error(data.error || 'No se pudo guardar.');
        }
        config = data.config || config;
        versions = data.versions || versions;
        setState(data.publicado_en ? 'Publicado' : 'Borrador guardado');
        renderAll();
        renderVersions();
        refreshRealPreview();
    }

    root.querySelector('[data-action="save"]')?.addEventListener('click', () => {
        postJson(root.dataset.saveUrl, { syncContent: true }).catch((error) => setState(error.message));
    });
    root.querySelector('[data-action="publish"]')?.addEventListener('click', () => {
        postJson(root.dataset.publishUrl, { syncContent: true }).catch((error) => setState(error.message));
    });
    root.querySelector('[data-apply-template]')?.addEventListener('click', () => {
        applyTemplate().catch((error) => setState(error.message));
    });

    root.querySelector('[data-asset-form]')?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const formData = new FormData(form);
        setState('Subiendo archivo...');
        const response = await fetch(root.dataset.uploadUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrfToken() },
            body: formData,
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setState(data.error || 'No se pudo subir.');
            return;
        }
        const assetList = root.querySelector('[data-asset-list]');
        const asset = data.asset;
        const item = document.createElement('article');
        item.dataset.assetId = asset.id;
        item.dataset.assetUrl = asset.url;
        item.dataset.assetTitle = asset.title;
        item.dataset.assetVideo = asset.isVideo ? '1' : '0';
        item.innerHTML = `
            ${asset.isVideo ? `<video src="${asset.url}" muted playsinline></video>` : `<img src="${asset.url}" alt="">`}
            <span>${escapeHtml(asset.title)}</span>
            ${assetTargetSelectHtml()}
            ${assetQuickTargetHtml()}
            <div class="asset-actions">
                <button type="button" data-asset-assign>Usar</button>
                <button type="button" data-asset-delete>Eliminar</button>
            </div>
        `;
        assetList.prepend(item);
        bindAssetItem(item);
        updateAssetDetailButtons();
        form.reset();
        setState('Archivo subido');
    });

    function assetTargetSelectHtml() {
        return `
            <select data-asset-target>
                <option value="TITULO_SECCION">Imagen completa</option>
                <option value="FONDO_SECCION">Fondo</option>
                <option value="CAPA_LIBRE">Capa</option>
                <option value="CEREMONIA">Foto ceremonia</option>
                <option value="RECEPCION">Foto recepcion</option>
                <option value="MAPA_CEREMONIA">Imagen mapa ceremonia</option>
                <option value="MAPA_RECEPCION">Imagen mapa recepcion</option>
                <option value="ALBUM">Álbum</option>
            </select>
        `;
    }

    function assetQuickTargetHtml() {
        return `
            <div class="asset-quick-targets">
                <button
                    type="button"
                    data-asset-quick-target="TITULO_SECCION"
                >
                    Imagen completa
                </button>

                <button
                    type="button"
                    data-asset-quick-target="FONDO_SECCION"
                >
                    Fondo
                </button>

                <button
                    type="button"
                    data-asset-quick-target="CAPA_LIBRE"
                >
                    Capa
                </button>
                <button
                    type="button"
                    data-asset-quick-target="COMPONENTE_IMAGEN"
                >
                    Imagen componente
                </button>

                <button
                    type="button"
                    data-asset-quick-target="CEREMONIA"
                    data-asset-details-only
                >
                    Foto ceremonia
                </button>

                <button
                    type="button"
                    data-asset-quick-target="RECEPCION"
                    data-asset-details-only
                >
                    Foto recepcion
                </button>

                <button
                    type="button"
                    data-asset-quick-target="MAPA_CEREMONIA"
                    data-asset-details-only
                >
                    Mapa ceremonia
                </button>

                <button
                    type="button"
                    data-asset-quick-target="MAPA_RECEPCION"
                    data-asset-details-only
                >
                    Mapa recepcion
                </button>

                <button
                    type="button"
                    data-asset-quick-target="ALBUM"
                >
                    Álbum
                </button>
            </div>
        `;
    }
    async function assignAsset(item) {
        return assignAssetRef(
            assetReferenceFromItem(item),
            item.querySelector('[data-asset-target]')?.value || 'FONDO_SECCION',
            selectedSection()
        );
    }


    function sectionUsesRealContent(sectionType) {
        return [
            'CUENTA_REGRESIVA',
            'DETALLES',
            'ALBUM',
            'REGALOS',
            'ALBUM_COMPARTIDO',
        ].includes(sectionType);
    }

    async function assignAssetRef(assetRef, destino, section) {
        const sectionDestinations = new Set([
            'FONDO_SECCION',
            'TITULO_SECCION',
            'CAPA_LIBRE',
            'COMPONENTE_IMAGEN',
            'MAPA_CEREMONIA',
            'MAPA_RECEPCION',
        ]);
        if (sectionDestinations.has(destino) && !section) {
            setState('Selecciona una seccion.');
            return;
        }
        if (['MAPA_CEREMONIA', 'MAPA_RECEPCION'].includes(destino) && section.type !== 'DETALLES') {
            setState('Selecciona la seccion Detalles para asignar esta imagen.');
            return;
        }
        if (destino === 'COMPONENTE_IMAGEN') {
            await createBuilderComponent('IMAGEN', {
                src: assetRef.url,
                alt: assetRef.title || 'Imagen',
                fit: 'contain',
            });
            return;
        }
        if (destino === 'FONDO_SECCION') {
            section.config = ensureSectionConfig(section);
            section.config.backgroundAsset = assetRef;
            section.config.showBackgroundLayer = true;
            section.config.backgroundOpacity = 1;
            section.config.backgroundBrightness = 1;
            section.config.backgroundBlur = 0;
        } else if (destino === 'TITULO_SECCION') {
            section.config = ensureSectionConfig(section);

            section.config.titleAsset = assetRef;
            section.config.showTitleAsset = true;

            section.config.layoutMode = 'full-image';
            section.config.keepRealContent = sectionUsesRealContent(section.type);
            section.config.showTextTitle = false;
            if (section.type === 'PORTADA') {
                config.theme = config.theme || {};
                config.theme.coverAsset = assetRef;
            }
            section.config.titleX = 50;
            section.config.titleY = 50;
            section.config.titleScale = 1;
            section.config.titleOpacity = 1;
            section.config.titleRotation = 0;
            section.config.titleWidth = 100;
            section.config.titleAlign = 'center';
            section.config.titleVisible = true;
            section.config.activeLayer = 'title';
        } else if (destino === 'CAPA_LIBRE') {
            addCustomLayer(section, {
                kind: assetRef.isVideo ? 'video' : 'image',
                name: assetRef.title || 'Imagen libre',
                asset: assetRef,
                x: 50,
                y: 50,
                width: 46,
                z: 5,
            });
            return;
        } else if (destino === 'ALBUM') {
            config.theme = config.theme || {};
            config.theme.albumAssets = config.theme.albumAssets || [];
            if (!config.theme.albumAssets.some((asset) => asset.id === assetRef.id)) {
                config.theme.albumAssets.push(assetRef);
            }
        } else if (destino === 'MAPA_CEREMONIA' || destino === 'MAPA_RECEPCION') {
            section.config = ensureSectionConfig(section);
            const real = normalizeRealContentConfig(section.config.realContent, section.type);
            const itemKey = destino === 'MAPA_CEREMONIA' ? 'ceremony' : 'reception';
            real.items[itemKey].mapAsset = assetRef;
            if (real.items[itemKey].mapDisplay === 'hidden') {
                real.items[itemKey].mapDisplay = 'map-only';
            }
            section.config.realContent = real;
        } else {
            const themeKey = {
                PORTADA: 'coverAsset',
                CEREMONIA: 'ceremonyAsset',
                RECEPCION: 'receptionAsset',
                DRESS_PERMITIDO: 'dressAllowedAsset',
                DRESS_PROHIBIDO: 'dressBlockedAsset',
            }[destino];
            config.theme = config.theme || {};
            config.theme[themeKey] = assetRef;
        }
        renderAll();
        setState('Asignando...');
        const response = await fetch(root.dataset.assignAssetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify({
                assetId: assetRef.id,
                destino,
                sectionId: section?.sectionId || null,
                layoutMode: section?.config?.layoutMode || 'normal',
                keepRealContent: section?.config?.keepRealContent ?? true,
                showTextTitle: section?.config?.showTextTitle ?? true,
            }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setState(data.error || 'No se pudo asignar.');
            return;
        }
        config = data.config || config;
        setState('Asignado al borrador');
        renderAll();
        refreshRealPreview();
    }

    async function deleteAsset(item) {
        setState('Eliminando archivo...');
        const response = await fetch(root.dataset.deleteAssetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken(),
            },
            body: JSON.stringify({ assetId: Number(item.dataset.assetId) }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) {
            setState(data.error || 'No se pudo eliminar.');
            return;
        }
        item.remove();
        setState('Archivo eliminado');
    }

    function bindAssetItem(item) {
        item.draggable = true;
        item.addEventListener('dragstart', (event) => {
            event.dataTransfer.setData('application/x-editor-asset', JSON.stringify(assetReferenceFromItem(item)));
            event.dataTransfer.effectAllowed = 'copy';
        });
        item.querySelector('[data-asset-assign]')?.addEventListener('click', () => {
            assignAsset(item).catch((error) => setState(error.message));
        });
        item.querySelectorAll('[data-asset-quick-target]').forEach((button) => {
            button.addEventListener('click', () => {
                assignAssetRef(assetReferenceFromItem(item), button.dataset.assetQuickTarget, selectedSection())
                    .catch((error) => setState(error.message));
            });
        });
        item.querySelector('[data-asset-delete]')?.addEventListener('click', () => {
            deleteAsset(item).catch((error) => setState(error.message));
        });
    }

    root.querySelectorAll('[data-asset-id]').forEach(bindAssetItem);

    root.querySelectorAll('[data-preview-mode]').forEach((button) => {
        button.addEventListener('click', () => {
            const mode = button.dataset.previewMode;
            currentPreviewMode = mode;

            root.querySelectorAll('[data-preview-mode]').forEach((item) => {
                item.classList.toggle('is-active', item === button);
            });

            root.querySelectorAll('[data-preview-panel]').forEach((panel) => {
                panel.hidden = panel.dataset.previewPanel !== mode;
            });

            if (mode === 'real') {
                refreshRealPreview();
                setLivePreviewMode(livePreviewMode);
            }

            updateEditorContextCard();
        });
    });

    root.querySelectorAll('[data-device-mode]').forEach((button) => {
        button.addEventListener('click', () => {
            const mode = button.dataset.deviceMode;
            currentDeviceMode = mode;
            root.querySelectorAll('[data-device-mode]').forEach((item) => item.classList.toggle('is-active', item === button));
            phonePreviews.forEach((preview) => {
                preview.dataset.device = mode;
            });
            setState(`Editando enfoque ${mode}`);
            renderAll();
        });
    });

    root.querySelectorAll('[data-live-preview-mode]').forEach((button) => {
        button.addEventListener('click', () => setLivePreviewMode(button.dataset.livePreviewMode));
    });

    realPreviewFrame?.addEventListener(
        'load',
        bindRealPreviewInteractions
    );

    /*
     * El iframe puede terminar de cargar antes de que este listener
     * sea conectado. En ese caso registramos inmediatamente.
     */
    if (
        realPreviewFrame?.contentDocument?.readyState === 'interactive' ||
        realPreviewFrame?.contentDocument?.readyState === 'complete'
    ) {
        bindRealPreviewInteractions();
    }

    setLivePreviewMode('edit');

    if (realPreviewFrame) {
        currentPreviewMode = 'real';

        root.querySelectorAll('[data-preview-mode]').forEach((button) => {
            button.classList.toggle(
                'is-active',
                button.dataset.previewMode === 'real'
            );
        });

        root.querySelectorAll('[data-preview-panel]').forEach((panel) => {
            panel.hidden = panel.dataset.previewPanel !== 'real';
        });
    }

    root.querySelectorAll('[data-content-tab]').forEach((button) => {
        button.addEventListener('click', () => {
            const target = button.dataset.contentTab;
            root.querySelectorAll('[data-content-tab]').forEach((item) => item.classList.toggle('is-active', item === button));
            root.querySelectorAll('[data-content-panel]').forEach((panel) => {
                panel.hidden = panel.dataset.contentPanel !== target;
            });
        });
    });

    root.querySelector('[data-content-form]')?.addEventListener('submit', (event) => {
        event.preventDefault();
        saveContent(formToObject(event.currentTarget)).catch((error) => setState(error.message));
    });

    root.querySelectorAll('[data-collection-form]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const collection = form.dataset.collectionForm;
            const payload = formToObject(form);
            saveCollectionItem(collection, payload)
                .then(() => form.reset())
                .catch((error) => setState(error.message));
        });
    });

    root.querySelector('[data-guest-group-form]')?.addEventListener('submit', (event) => {
        event.preventDefault();
        saveGuestGroup(formToObject(event.currentTarget))
            .then(() => event.currentTarget.reset())
            .catch((error) => setState(error.message));
    });

    root.querySelector('[data-guest-person-form]')?.addEventListener('submit', (event) => {
        event.preventDefault();
        saveGuestPerson(formToObject(event.currentTarget))
            .then(() => event.currentTarget.reset())
            .catch((error) => setState(error.message));
    });

    root.querySelector('[data-guest-import-form]')?.addEventListener('submit', (event) => {
        event.preventDefault();
        importGuests(event.currentTarget)
            .then(() => event.currentTarget.reset())
            .catch((error) => setState(error.message));
    });

    renderContent();
    renderGuests();
    renderVersions();
    ensureEditorUiIntegrity();
    installSimplifiedEditorUi();
    renderAll();

    window.DIRTECNativeElements = Object.freeze({
        list: () => nativeElementRegistry.map(
            ({ id, type, role, section, item }) => ({
                id,
                type,
                role,
                section,
                item,
            })
        ),
        get: (elementId) => {
            const element = nativeElementById(elementId);

            if (!element) return null;

            return {
                id: element.id,
                type: element.type,
                role: element.role,
                section: element.section,
                item: element.item,
            };
        },
        count: () => nativeElementRegistry.length,
    });

    loadBuilderComponents().catch((error) => setState(error.message));
}());