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
    let selectedId = config.sections?.[0]?.sectionId || null;
    const layerBounds = { min: -40, max: 140 };

    const sectionList = root.querySelector('[data-section-list]');
    const previewRoot = root.querySelector('[data-preview-root]');
    const saveState = root.querySelector('[data-save-state]');
    const sectionProps = root.querySelector('[data-section-properties]');
    const versionList = root.querySelector('[data-version-list]');
    const guestList = root.querySelector('[data-guest-list]');
    const phonePreviews = root.querySelectorAll('.phone-preview');

    function defaultSectionConfig() {
        return {
            textAlign: 'center',
            titleSize: 'medium',
            backgroundOpacity: '0.18',
            backgroundPosition: 'center center',
            textColor: '',
            showTextTitle: true,
            backgroundAsset: {},
            titleAsset: {},
            backgroundFit: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundX: 50,
            backgroundY: 50,
            backgroundScale: 1,
            backgroundBrightness: 1,
            backgroundBlur: 0,
            sectionHeight: 190,
            activeLayer: 'background',
            showBackgroundLayer: true,
            showTitleAsset: true,
            titleX: 50,
            titleY: 50,
            titleScale: 1,
            titleOpacity: 1,
            titleVisible: true,
            titleRotation: 0,
            titleLocked: false,
            titleZ: 2,
            titleWidth: 72,
            titleAlign: 'center',
            textX: 50,
            textY: 50,
            textScale: 1,
            textOpacity: 1,
            textVisible: true,
            textRotation: 0,
            textLocked: false,
            textZ: 2,
            textWidth: 78,
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

    function refreshRealPreview() {
        const frame = root.querySelector('[data-real-preview-frame]');
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
        const scale = clamp(cfg.backgroundScale ?? 1, 0.4, 3);
        if (cfg.backgroundFit === 'cover') return `auto ${Math.round(scale * 100)}%`;
        if (cfg.backgroundFit === 'repeat') return `${Math.max(Math.round(scale * 140), 40)}px auto`;
        if (cfg.backgroundFit === 'free') return `${Math.max(Math.round(scale * 100), 40)}% auto`;
        return 'contain';
    }

    function backgroundRepeatValue(cfg) {
        return cfg.backgroundFit === 'repeat' || cfg.backgroundRepeat === 'repeat' ? 'repeat' : 'no-repeat';
    }

    function setBackgroundStyles(layer, cfg, asset) {
        layer.style.opacity = String(clamp(cfg.backgroundOpacity ?? 0.18, 0, 1));
        layer.style.backgroundSize = backgroundSizeValue(cfg);
        layer.style.backgroundRepeat = backgroundRepeatValue(cfg);
        layer.style.backgroundPosition = `${clamp(cfg.backgroundX ?? 50, 0, 100)}% ${clamp(cfg.backgroundY ?? 50, 0, 100)}%`;
        layer.style.filter = `brightness(${clamp(cfg.backgroundBrightness ?? 1, 0.35, 1.75)}) blur(${clamp(cfg.backgroundBlur ?? 0, 0, 12)}px)`;
        if (asset?.url && !asset.isVideo) {
            layer.style.backgroundImage = `url("${asset.url}")`;
        }
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

    function bindRealPreviewInteractions() {
        const frame = root.querySelector('[data-real-preview-frame]');
        if (!frame) return;
        try {
            const doc = frame.contentDocument;
            if (!doc.getElementById('editor-real-preview-style')) {
                const style = doc.createElement('style');
                style.id = 'editor-real-preview-style';
                style.textContent = `
                    [data-invitation-section] { cursor: crosshair; }
                    .editor-real-selected {
                        outline: 2px solid rgba(199, 125, 146, .72) !important;
                        outline-offset: -4px !important;
                    }
                    .editor-real-layer {
                        outline: 2px dashed rgba(38, 49, 38, .72) !important;
                        outline-offset: 5px !important;
                    }
                    .custom-public-layer { pointer-events: auto !important; }
                `;
                doc.head.appendChild(style);
            }
            const paintSelection = (sectionEl, layerEl) => {
                doc.querySelectorAll('.editor-real-selected').forEach((item) => item.classList.remove('editor-real-selected'));
                doc.querySelectorAll('.editor-real-layer').forEach((item) => item.classList.remove('editor-real-layer'));
                sectionEl.classList.add('editor-real-selected');
                if (layerEl) layerEl.classList.add('editor-real-layer');
            };
            const layerFromTarget = (target) => {
                const custom = target.closest('.custom-public-layer[data-editor-layer]');
                if (custom) return { layer: custom.dataset.editorLayer, element: custom };
                const title = target.closest('.section-title, .section-title-image, .cover-names, .cover-topline, .cover-date');
                if (title) return { layer: 'title', element: title };
                const text = target.closest('.section-copy, .event-detail-grid, .count-grid, .dress-visual, .menu-grid, .gift-grid, .album-grid, .form-grid, .guest-box, .cover-honors, .itinerary-list');
                if (text) return { layer: 'text', element: text };
                return { layer: 'background', element: null };
            };
            doc.querySelectorAll('[data-invitation-section]').forEach((sectionEl) => {
                sectionEl.style.cursor = 'pointer';
                sectionEl.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    const selected = layerFromTarget(event.target);
                    selectSectionByType(sectionEl.dataset.invitationSection, selected.layer);
                    paintSelection(sectionEl, selected.element);
                    setState(`Vista real: ${sectionEl.dataset.invitationSection.replaceAll('_', ' ')} / ${selected.layer.replace('custom:', 'capa ')}`);
                });
            });
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
            const thumb = document.createElement('span');
            thumb.className = 'section-thumb';
            if (background.url && !background.isVideo) thumb.style.backgroundImage = `url("${background.url}")`;
            if (background.isVideo) thumb.textContent = 'Video';
            item.insertBefore(thumb, mainButton);
            item.querySelector('.section-main').addEventListener('click', () => {
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
            article.style.minHeight = `${clamp(cfg.sectionHeight ?? 190, 120, 900)}px`;
            if (cfg.textColor) article.style.color = cfg.textColor;
            const background = cfg.backgroundAsset || {};
            const titleAsset = cfg.titleAsset || {};
            if (cfg.showBackgroundLayer !== false && background.url && background.isVideo) {
                const video = document.createElement('video');
                video.className = 'preview-section-media';
                video.src = background.url;
                video.autoplay = true;
                video.muted = true;
                video.loop = true;
                video.playsInline = true;
                video.style.opacity = String(clamp(cfg.backgroundOpacity ?? 0.18, 0, 1));
                video.style.objectFit = cfg.backgroundFit === 'cover' ? 'cover' : 'contain';
                video.style.objectPosition = `${clamp(cfg.backgroundX ?? 50, 0, 100)}% ${clamp(cfg.backgroundY ?? 50, 0, 100)}%`;
                video.style.filter = `brightness(${clamp(cfg.backgroundBrightness ?? 1, 0.35, 1.75)}) blur(${clamp(cfg.backgroundBlur ?? 0, 0, 12)}px)`;
                article.appendChild(video);
            }
            const bgLayer = document.createElement('div');
            bgLayer.className = 'preview-section-bg';
            bgLayer.classList.toggle('is-hidden', cfg.showBackgroundLayer === false);
            if (cfg.showBackgroundLayer !== false) setBackgroundStyles(bgLayer, cfg, background);
            attachBackgroundDrag(article, bgLayer, section, cfg);
            article.appendChild(bgLayer);
            const decorLayer = document.createElement('div');
            decorLayer.className = 'preview-layer preview-decor-layer';
            decorLayer.dataset.layer = 'decor';
            decorLayer.textContent = decorText(cfg.decorStyle);
            setLayerStyles(decorLayer, cfg, 'decor');
            attachLayerDrag(article, decorLayer, section, cfg, 'decor');
            article.appendChild(decorLayer);

            const titleLayer = document.createElement('div');
            titleLayer.className = 'preview-layer preview-title-layer';
            titleLayer.dataset.layer = 'title';
            if (titleAsset.url && cfg.showTitleAsset !== false) {
                titleLayer.insertAdjacentHTML('beforeend', titleAsset.isVideo
                    ? `<video class="preview-title-asset" src="${titleAsset.url}" autoplay muted loop playsinline></video>`
                    : `<img class="preview-title-asset" src="${titleAsset.url}" alt="">`);
            }
            if (cfg.showTextTitle !== false) {
                const title = document.createElement('h2');
                title.textContent = section.title || '';
                titleLayer.appendChild(title);
            }
            setLayerStyles(titleLayer, cfg, 'title');
            attachLayerDrag(article, titleLayer, section, cfg, 'title');
            article.appendChild(titleLayer);

            const textLayer = document.createElement('div');
            textLayer.className = 'preview-layer preview-text-layer';
            textLayer.dataset.layer = 'text';
            const copy = document.createElement('div');
            copy.className = 'preview-real-data';
            copy.innerHTML = sectionPreviewHtml(section);
            textLayer.appendChild(copy);
            setLayerStyles(textLayer, cfg, 'text');
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
            article.addEventListener('click', () => {
                selectedId = section.sectionId;
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
                startX: clamp(cfg.backgroundX ?? 50, 0, 100),
                startY: clamp(cfg.backgroundY ?? 50, 0, 100),
                width: Math.max(article.clientWidth, 1),
                height: Math.max(article.clientHeight, 1),
            };
            bgLayer.setPointerCapture(event.pointerId);
        });
        bgLayer.addEventListener('pointermove', (event) => {
            if (!dragging) return;
            const deltaX = ((event.clientX - dragging.x) / dragging.width) * 100;
            const deltaY = ((event.clientY - dragging.y) / dragging.height) * 100;
            cfg.backgroundX = Math.round(clamp(dragging.startX + deltaX, 0, 100));
            cfg.backgroundY = Math.round(clamp(dragging.startY + deltaY, 0, 100));
            setBackgroundStyles(bgLayer, cfg, cfg.backgroundAsset || {});
            const xField = root.querySelector('[data-config-field="backgroundX"]');
            const yField = root.querySelector('[data-config-field="backgroundY"]');
            if (xField) xField.value = cfg.backgroundX;
            if (yField) yField.value = cfg.backgroundY;
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
    }

    function renderAll() {
        applyTheme();
        renderSectionList();
        renderPreview();
        fillProperties();
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
        const people = (first.guests || []).slice(0, 4).map((guest) => `
            <span>${escapeHtml(guest.name)} <small>${escapeHtml(guest.type || '')}</small></span>
        `).join('');
        return `
            <div class="preview-rsvp-box">
                <strong>${escapeHtml(first.type === 'FAMILIAR' ? `Familia ${first.name}` : first.name)}</strong>
                <span>${escapeHtml(first.places)} lugar(es) - ${escapeHtml(first.adults)} adulto(s) - ${escapeHtml(first.children)} nino(s)</span>
                ${people ? `<div class="preview-rsvp-people">${people}</div>` : ''}
            </div>
        `;
    }

    function sectionPreviewHtml(section) {
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
                    ${namesPreview()}
                    <div><span>244</span><span>23</span><span>31</span><span>49</span></div>
                    <small>${escapeHtml(formatDateTime(event.receptionDate || event.ceremonyDate))}</small>
                </div>
            `;
        }
        if (section.type === 'DETALLES') {
            return `
                ${description}
                <div class="preview-detail-grid">
                    <div><strong>Ceremonia</strong><span>${escapeHtml(formatDateTime(event.ceremonyDate))}</span><p>${escapeHtml(event.ceremonyPlace || 'Templo por confirmar')}</p><small>${escapeHtml(event.ceremonyAddress || '')}</small></div>
                    <div><strong>Recepcion</strong><span>${escapeHtml(formatDateTime(event.receptionDate))}</span><p>${escapeHtml(event.receptionPlace || 'Salon por confirmar')}</p><small>${escapeHtml(event.receptionAddress || '')}</small></div>
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
            return previewList(content.gifts, 'Sin mesa de regalos visible', (item) => `<div><strong>${escapeHtml(item.name || item.typeLabel || 'Regalo')}</strong><span>${escapeHtml(item.bank || item.url || item.instructions || '')}</span></div>`, 4);
        }
        if (section.type === 'ALBUM_COMPARTIDO') {
            return `<p>${escapeHtml(event.sharedAlbumText || section.description || 'Comparte tus fotos y videos en el album del evento.')}</p><small>${escapeHtml(event.sharedAlbumUrl || 'Link por configurar')}</small>`;
        }
        if (section.type === 'RSVP') {
            return `${description || `<p>${escapeHtml(event.rsvpText || 'Confirma tu asistencia.')}</p>`}${previewGuestSummary()}`;
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
            section.config[field.dataset.configField] = field.type === 'checkbox' ? field.checked : field.value;
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
            backgroundOpacity: 0.18,
            backgroundBrightness: 1,
            backgroundBlur: 0,
            sectionHeight: 190,
        });
        setState('Imagen reajustada');
        renderAll();
    });

    async function postJson(url) {
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
        postJson(root.dataset.saveUrl).catch((error) => setState(error.message));
    });
    root.querySelector('[data-action="publish"]')?.addEventListener('click', () => {
        postJson(root.dataset.publishUrl).catch((error) => setState(error.message));
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
        form.reset();
        setState('Archivo subido');
    });

    function assetTargetSelectHtml() {
        return `
            <select data-asset-target>
                <option value="FONDO_SECCION">Fondo seccion</option>
                <option value="TITULO_SECCION">Imagen titulo</option>
                <option value="PORTADA">Portada principal</option>
                <option value="CEREMONIA">Portada templo</option>
                <option value="RECEPCION">Portada fiesta</option>
                <option value="DRESS_PERMITIDO">Dress permitido</option>
                <option value="DRESS_PROHIBIDO">Dress prohibido</option>
                <option value="CAPA_LIBRE">Capa libre</option>
                <option value="ALBUM">Agregar al album</option>
            </select>
        `;
    }

    function assetQuickTargetHtml() {
        return `
            <div class="asset-quick-targets">
                <button type="button" data-asset-quick-target="CAPA_LIBRE">Capa</button>
                <button type="button" data-asset-quick-target="FONDO_SECCION">Fondo</button>
                <button type="button" data-asset-quick-target="TITULO_SECCION">Titulo</button>
                <button type="button" data-asset-quick-target="PORTADA">Portada</button>
                <button type="button" data-asset-quick-target="ALBUM">Album</button>
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

    async function assignAssetRef(assetRef, destino, section) {
        if ((destino === 'FONDO_SECCION' || destino === 'TITULO_SECCION' || destino === 'CAPA_LIBRE') && !section) {
            setState('Selecciona una seccion.');
            return;
        }
        if (destino === 'FONDO_SECCION') {
            section.config = ensureSectionConfig(section);
            section.config.backgroundAsset = assetRef;
            section.config.showBackgroundLayer = true;
        } else if (destino === 'TITULO_SECCION') {
            section.config = ensureSectionConfig(section);
            section.config.titleAsset = assetRef;
            section.config.showTitleAsset = true;
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
            root.querySelectorAll('[data-preview-mode]').forEach((item) => item.classList.toggle('is-active', item === button));
            root.querySelectorAll('[data-preview-panel]').forEach((panel) => {
                panel.hidden = panel.dataset.previewPanel !== mode;
            });
            if (mode === 'real') refreshRealPreview();
        });
    });

    root.querySelectorAll('[data-device-mode]').forEach((button) => {
        button.addEventListener('click', () => {
            const mode = button.dataset.deviceMode;
            root.querySelectorAll('[data-device-mode]').forEach((item) => item.classList.toggle('is-active', item === button));
            phonePreviews.forEach((preview) => {
                preview.dataset.device = mode;
            });
        });
    });

    root.querySelector('[data-real-preview-frame]')?.addEventListener('load', bindRealPreviewInteractions);

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
    renderAll();
}());
