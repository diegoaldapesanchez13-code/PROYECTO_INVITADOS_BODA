import { BuilderApp } from "../../app/index.js";
import {
    createDjangoPersistenceAdapter,
    registerPersistenceModule,
} from "../../persistence/index.js";
import { registerMigrationModule } from "../../migration/index.js";
import {
    CanvasWorkspaceController,
    renderCanvasPreview,
} from "../../workspace/index.js";

const root = document.querySelector("[data-builder-engine-root]");

if (root) {
    mountBuilderEngine(root).catch((error) => {
        console.error("No fue posible iniciar DIRTEC Builder Engine.", error);
        setStatus(root, "ERROR", error.message || "Error al iniciar el editor.");
    });
}

async function mountBuilderEngine(root) {
    const config = readBootstrap(root);
    const documentInfo = root.querySelector("[data-engine-document-info]");
    const migrationNotice = root.querySelector("[data-engine-migration-notice]");
    const canvasNavigator = root.querySelector("[data-engine-canvas-nav]");
    const canvasStage = root.querySelector("[data-engine-active-canvas]");
    const inspectorTitle = root.querySelector("[data-engine-inspector-title]");
    const inspectorName = root.querySelector("[data-engine-canvas-name]");
    const saveButton = root.querySelector("[data-engine-action='save']");
    const publishButton = root.querySelector("[data-engine-action='publish']");
    const reloadButton = root.querySelector("[data-engine-action='reload']");

    const persistencePort = createDjangoPersistenceAdapter({
        endpoints: config.endpoints,
        csrfToken: getCsrfToken(),
    });

    const app = new BuilderApp({ eventId: config.eventId });
    const persistenceModule = registerPersistenceModule(app, {
        port: persistencePort,
        autosave: true,
        autosaveDelay: 3000,
        workspaceState: { previewDevice: "iphone-13" },
    });
    const migrationModule = registerMigrationModule(app);

    await app.start();
    await persistenceModule.service.load();

    const migrationReport = migrationModule.migrateIfNeeded(app);
    if (migrationReport.migrated) {
        showMigrationNotice(migrationNotice, migrationReport);
        await persistenceModule.service.save({
            reason: "legacy-schema-migration",
        });
    }

    const workspaceController = new CanvasWorkspaceController({
        app,
        workspace: persistenceModule.workspace,
    }).initialize();

    const render = () => {
        const documentValue = app.getDocument();
        renderDocumentInfo(documentInfo, documentValue);
        renderCanvasNavigator(
            canvasNavigator,
            workspaceController.list(),
            workspaceController.selectedCanvasId,
        );
        renderSelectedCanvas(
            canvasStage,
            workspaceController.getSelected(),
            documentValue.assets || [],
        );
        renderCanvasInspector(
            inspectorTitle,
            inspectorName,
            workspaceController.getSelected(),
        );
        root.dataset.dirty = app.isDirty ? "true" : "false";
    };

    root.addEventListener("click", async (event) => {
        const button = event.target.closest("[data-engine-canvas-action]");
        if (!button) return;

        const action = button.dataset.engineCanvasAction;
        const canvasId = button.dataset.canvasId;

        try {
            if (action === "select") workspaceController.select(canvasId);
            if (action === "create") workspaceController.create();
            if (action === "duplicate") workspaceController.duplicate(canvasId);
            if (action === "delete") {
                if (window.confirm("¿Eliminar este lienzo?")) {
                    workspaceController.remove(canvasId);
                }
            }
            if (action === "up") workspaceController.move(canvasId, "up");
            if (action === "down") workspaceController.move(canvasId, "down");
            if (action === "visibility") workspaceController.toggleVisibility(canvasId);
            render();
        } catch (error) {
            window.alert(error.message || "No fue posible completar la acción.");
        }
    });

    inspectorName?.addEventListener("change", () => {
        const selected = workspaceController.getSelected();
        if (!selected) return;
        workspaceController.rename(selected.id, inspectorName.value);
    });

    app.subscribe((event) => {
        if (["document:changed", "document:replaced", "document:saved"].includes(event.type)) {
            if (!workspaceController.getSelected()) workspaceController.initialize();
            render();
        }
    });

    persistenceModule.service.subscribe((state) => {
        const messages = {
            IDLE: "Listo",
            LOADING: "Cargando…",
            SAVING: "Guardando…",
            SAVED: state.dirty ? "Cambios pendientes" : "Guardado",
            PUBLISHING: "Publicando…",
            PUBLISHED: "Publicado",
            ERROR: state.lastError?.message || "Error",
        };
        setStatus(root, state.status, messages[state.status] || state.status);
        if (saveButton) saveButton.disabled = state.status === "SAVING";
        if (publishButton) publishButton.disabled = state.status === "PUBLISHING";
    });

    saveButton?.addEventListener("click", () =>
        persistenceModule.service.save({ reason: "manual" })
    );

    publishButton?.addEventListener("click", async () => {
        if (!window.confirm("¿Publicar este documento?")) return;
        await persistenceModule.service.publish();
    });

    reloadButton?.addEventListener("click", async () => {
        if (
            app.isDirty
            && !window.confirm("Hay cambios pendientes. ¿Recargar el borrador guardado?")
        ) return;
        await persistenceModule.service.load();
        migrationModule.migrateIfNeeded(app);
        workspaceController.initialize();
        render();
    });

    window.DIRTEC_BUILDER = Object.freeze({
        app,
        persistence: persistenceModule.service,
        workspace: persistenceModule.workspace,
        migration: migrationModule,
        canvasWorkspace: workspaceController,
        config,
    });

    render();
    setStatus(root, "SAVED", "Builder Engine conectado");
}

function renderCanvasNavigator(node, canvases, selectedId) {
    if (!node) return;

    node.innerHTML = `
        <div class="engine-canvas-nav-head">
            <strong>Lienzos</strong>
            <button type="button" data-engine-canvas-action="create">＋</button>
        </div>
        <div class="engine-canvas-nav-list">
            ${canvases.map((canvas, index) => `
                <article class="engine-canvas-nav-item ${canvas.id === selectedId ? "active" : ""}">
                    <button
                        class="engine-canvas-select"
                        type="button"
                        data-engine-canvas-action="select"
                        data-canvas-id="${escapeHtml(canvas.id)}"
                    >
                        <span>${index + 1}</span>
                        <div>
                            <strong>${escapeHtml(canvas.name || `Lienzo ${index + 1}`)}</strong>
                            <small>${escapeHtml(canvas.type || "PERSONALIZADA")}</small>
                        </div>
                    </button>
                    <div class="engine-canvas-item-actions">
                        <button type="button" title="Subir" data-engine-canvas-action="up" data-canvas-id="${escapeHtml(canvas.id)}">↑</button>
                        <button type="button" title="Bajar" data-engine-canvas-action="down" data-canvas-id="${escapeHtml(canvas.id)}">↓</button>
                        <button type="button" title="Duplicar" data-engine-canvas-action="duplicate" data-canvas-id="${escapeHtml(canvas.id)}">⧉</button>
                        <button type="button" title="Mostrar u ocultar" data-engine-canvas-action="visibility" data-canvas-id="${escapeHtml(canvas.id)}">${canvas.visible === false ? "○" : "●"}</button>
                        <button type="button" title="Eliminar" data-engine-canvas-action="delete" data-canvas-id="${escapeHtml(canvas.id)}">×</button>
                    </div>
                </article>
            `).join("")}
        </div>
    `;
}

function renderSelectedCanvas(node, canvas, assets) {
    if (!node) return;
    node.innerHTML = "";
    if (!canvas) {
        node.innerHTML = '<div class="engine-live-empty"><strong>Sin lienzo seleccionado</strong></div>';
        return;
    }
    node.appendChild(renderCanvasPreview(canvas, { assets }));
}

function renderCanvasInspector(titleNode, nameInput, canvas) {
    if (titleNode) titleNode.textContent = canvas ? "Propiedades del lienzo" : "Sin selección";
    if (nameInput) {
        nameInput.disabled = !canvas;
        nameInput.value = canvas?.name || "";
    }
}

function showMigrationNotice(node, report) {
    if (!node) return;
    node.hidden = false;
    node.innerHTML = `
        <strong>Diseño anterior migrado correctamente</strong>
        <span>${report.canvases} lienzos · ${report.nodes} elementos · ${report.assets} assets</span>
    `;
}

function readBootstrap(root) {
    const script = document.getElementById(root.dataset.bootstrapId);
    if (!script) throw new Error("No se encontró la configuración de arranque.");
    const config = JSON.parse(script.textContent || "{}");
    if (!config.eventId) throw new Error("eventId es obligatorio.");
    for (const name of ["load", "save", "publish"]) {
        if (!config.endpoints?.[name]) throw new Error(`Falta endpoint: ${name}.`);
    }
    return config;
}

function renderDocumentInfo(node, documentValue) {
    if (!node) return;
    const metadata = documentValue.metadata || {};
    node.innerHTML = `
        <strong>${escapeHtml(metadata.name || "Documento sin título")}</strong>
        <span>Schema ${Number(documentValue.schemaVersion || 0)}</span>
        <span>Documento v${Number(documentValue.documentVersion || 1)}</span>
        <span>Builder ${escapeHtml(documentValue.builderVersion || "—")}</span>
    `;
}

function setStatus(root, status, message) {
    root.dataset.status = status;
    const node = root.querySelector("[data-engine-status]");
    if (node) {
        node.textContent = message;
        node.dataset.status = status;
    }
}

function getCsrfToken() {
    const input = document.querySelector("input[name='csrfmiddlewaretoken']");
    if (input?.value) return input.value;
    const cookie = document.cookie
        .split(";")
        .map((item) => item.trim())
        .find((item) => item.startsWith("csrftoken="));
    return cookie ? decodeURIComponent(cookie.split("=").slice(1).join("=")) : "";
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
