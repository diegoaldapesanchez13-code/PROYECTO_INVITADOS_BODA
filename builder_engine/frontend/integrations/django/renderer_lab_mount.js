import {
    UniversalDomAdapter,
    UniversalRenderer,
    createUniversalRendererFixture,
} from "../../renderer/index.js";

const MODES = ["EDIT", "PREVIEW", "PUBLIC"];
const DEVICES = {
    mobile: { label: "Celular", width: 390 },
    tablet: { label: "Tablet", width: 768 },
    desktop: { label: "Desktop", width: 1180 },
};

boot().catch((error) => {
    console.error("Renderer Lab no pudo iniciar.", error);
    setStatus(error.message || "No fue posible iniciar el laboratorio.", "error");
});

async function boot() {
    const root = document.querySelector("[data-renderer-lab-root]");
    const bootstrapElement = document.getElementById(
        root?.dataset.bootstrapId || "dirtec-renderer-lab-bootstrap"
    );
    if (!root || !bootstrapElement) {
        throw new Error("No se encontró la configuración del Renderer Lab.");
    }

    const config = JSON.parse(bootstrapElement.textContent || "{}");
    const state = {
        device: "mobile",
        document: null,
        usingFixture: false,
        renderer: new UniversalRenderer(),
    };

    bindControls(root, state);
    state.document = await loadDocument(config, state);
    renderAll(root, state);

    const observer = new ResizeObserver(() => scaleAll(root));
    for (const viewport of root.querySelectorAll("[data-renderer-viewport]")) {
        observer.observe(viewport);
    }

    window.DIRTEC_RENDERER_LAB = Object.freeze({
        state,
        render: () => renderAll(root, state),
        setDevice(device) {
            if (!DEVICES[device]) throw new Error("Dispositivo no soportado.");
            state.device = device;
            renderAll(root, state);
        },
    });
}

async function loadDocument(config, state) {
    setStatus("Cargando documento real…", "loading");
    const response = await fetch(config.endpoints.load, {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
    });

    let payload;
    try { payload = await response.json(); }
    catch { throw new Error(`El endpoint respondió con formato inválido (HTTP ${response.status}).`); }

    if (!response.ok || !payload.ok) {
        throw new Error(payload.error || `No se pudo cargar el documento (HTTP ${response.status}).`);
    }

    const document = payload.document || {};
    if (!Array.isArray(document.canvases) || document.canvases.length === 0) {
        state.usingFixture = true;
        setStatus("El documento no tiene lienzos. Se muestra el fixture del Universal Renderer.", "warning");
        return createUniversalRendererFixture();
    }

    state.usingFixture = false;
    setStatus(`${document.canvases.length} lienzos cargados · Documento real · Solo lectura`, "success");
    return document;
}

function bindControls(root, state) {
    root.addEventListener("click", (event) => {
        const deviceButton = event.target.closest("[data-renderer-device]");
        if (deviceButton) {
            state.device = deviceButton.dataset.rendererDevice;
            renderAll(root, state);
            return;
        }
        if (event.target.closest("[data-renderer-reload]")) window.location.reload();
    });
}

function renderAll(root, state) {
    updateDeviceControls(root, state.device);
    root.dataset.device = state.device;
    root.dataset.fixture = state.usingFixture ? "true" : "false";

    for (const mode of MODES) {
        const target = root.querySelector(`[data-renderer-target="${mode}"]`);
        const metadata = root.querySelector(`[data-renderer-meta="${mode}"]`);
        if (!target) continue;

        const result = state.renderer.renderDocument(state.document, { mode, device: state.device });
        new UniversalDomAdapter({ runtime: createLabRuntime(mode) }).mount(result, target);

        if (metadata) {
            const first = result.canvases[0];
            metadata.textContent = [
                DEVICES[state.device].label,
                `${result.canvases.length} lienzos`,
                first ? `${first.width} × ${first.height}px` : "sin lienzos",
                result.metadata.interactive ? "interactivo" : "edición segura",
            ].join(" · ");
        }
    }
    requestAnimationFrame(() => scaleAll(root));
}

function createLabRuntime(mode) {
    const announce = (label, value) => setStatus(`[${mode}] ${label}: ${value || ""}`, "action");
    return {
        openUrl: (value) => announce("Abrir URL", value),
        navigate: (value) => announce("Navegar", value),
        openRsvp: (payload) => announce("Abrir RSVP", JSON.stringify(payload || {})),
        openModal: (value) => announce("Abrir modal", value),
        download: (value) => announce("Descargar", value),
        playMedia: (value) => announce("Reproducir media", value),
    };
}

function scaleAll(root) {
    for (const viewport of root.querySelectorAll("[data-renderer-viewport]")) {
        const target = viewport.querySelector("[data-renderer-target]");
        const canvas = target?.querySelector(".dirtec-render-canvas");
        if (!target || !canvas) {
            viewport.style.setProperty("--renderer-lab-height", "180px");
            continue;
        }
        const available = Math.max(viewport.clientWidth - 24, 1);
        const logicalWidth = Number.parseFloat(canvas.style.width) || canvas.offsetWidth || 390;
        const logicalHeight = Number.parseFloat(canvas.style.height) || canvas.offsetHeight || 844;
        const scale = Math.min(1, available / logicalWidth);
        target.style.transform = `scale(${scale})`;
        target.style.transformOrigin = "top center";
        target.style.width = `${logicalWidth}px`;
        viewport.style.setProperty("--renderer-lab-height", `${Math.max(logicalHeight * scale + 24, 180)}px`);
        viewport.dataset.scale = scale.toFixed(3);
    }
}

function updateDeviceControls(root, device) {
    for (const button of root.querySelectorAll("[data-renderer-device]")) {
        const active = button.dataset.rendererDevice === device;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
    }
}

function setStatus(message, type = "info") {
    const status = document.querySelector("[data-renderer-lab-status]");
    if (!status) return;
    status.textContent = message;
    status.dataset.type = type;
}
