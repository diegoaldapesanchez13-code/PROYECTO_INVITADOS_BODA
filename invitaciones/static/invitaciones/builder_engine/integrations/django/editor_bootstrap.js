import { BuilderApp } from "../../app/index.js";
import {
    createDjangoPersistenceAdapter,
    registerPersistenceModule,
} from "../../persistence/index.js";
import { registerMigrationModule } from "../../migration/index.js";
import {
    CanvasWorkspaceController,
    NodeWorkspaceController,
    renderCanvasPreview,
    renderLayersTree,
    renderNodeInspector,
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
    const layersPanel = root.querySelector("[data-engine-layers-panel]");
    const nodeInspector = root.querySelector("[data-engine-node-inspector]");
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
        await persistenceModule.service.save({ reason: "legacy-schema-migration" });
    }

    const canvasController = new CanvasWorkspaceController({
        app,
        workspace: persistenceModule.workspace,
    }).initialize();

    const nodeController = new NodeWorkspaceController({
        app,
        workspace: persistenceModule.workspace,
        canvasController,
    }).initialize();

    const render = () => {
        const documentValue = app.getDocument();
        const selectedCanvas = canvasController.getSelected();

        renderDocumentInfo(documentInfo, documentValue);
        renderCanvasNavigator(
            canvasNavigator,
            canvasController.list(),
            canvasController.selectedCanvasId,
        );
        renderLayersTree(
            layersPanel,
            selectedCanvas?.nodes || [],
            { selectedId: nodeController.selectedNodeId },
        );
        renderSelectedCanvas(
            canvasStage,
            selectedCanvas,
            documentValue.assets || [],
            nodeController.selectedNodeId,
        );
        renderNodeInspector(nodeInspector, nodeController.getSelected());
        root.dataset.dirty = app.isDirty ? "true" : "false";
    };

    root.addEventListener("click", (event) => {
        const canvasButton = event.target.closest("[data-engine-canvas-action]");
        const nodeButton = event.target.closest("[data-engine-node-action]");

        try {
            if (canvasButton) {
                const action = canvasButton.dataset.engineCanvasAction;
                const canvasId = canvasButton.dataset.canvasId;

                if (action === "select") {
                    canvasController.select(canvasId);
                    nodeController.select(null);
                }
                if (action === "create") {
                    canvasController.create();
                    nodeController.select(null);
                }
                if (action === "duplicate") canvasController.duplicate(canvasId);
                if (action === "delete" && window.confirm("¿Eliminar este lienzo?")) {
                    canvasController.remove(canvasId);
                    nodeController.select(null);
                }
                if (action === "up") canvasController.move(canvasId, "up");
                if (action === "down") canvasController.move(canvasId, "down");
                if (action === "visibility") canvasController.toggleVisibility(canvasId);
            }

            if (nodeButton) {
                const action = nodeButton.dataset.engineNodeAction;
                const nodeId = nodeButton.dataset.nodeId;

                if (action === "select") nodeController.select(nodeId);
                if (action === "visibility") nodeController.toggleVisibility();
                if (action === "lock") nodeController.toggleLock();
                if (action === "delete" && window.confirm("¿Eliminar este elemento?")) {
                    nodeController.remove();
                }
            }

            render();
        } catch (error) {
            window.alert(error.message || "No fue posible completar la acción.");
        }
    });

    root.addEventListener("input", (event) => {
        const field = event.target.closest("[data-node-field]");
        if (!field) return;

        const path = field.dataset.nodeField;
        let value = field.value;
        if (field.type === "number") value = Number(field.value);

        try {
            if (path === "name") nodeController.rename(value);
            else if (path === "style.zIndex") nodeController.setZIndex(value);
            else nodeController.update(path, value);
            render();
        } catch (error) {
            console.error(error);
        }
    });

    app.subscribe((event) => {
        if (["document:changed", "document:replaced", "document:saved"].includes(event.type)) {
            if (!canvasController.getSelected()) canvasController.initialize();
            if (nodeController.selectedNodeId && !nodeController.getSelected()) {
                nodeController.select(null);
            }
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
        canvasController.initialize();
        nodeController.initialize();
        render();
    });

    window.DIRTEC_BUILDER = Object.freeze({
        app,
        persistence: persistenceModule.service,
        workspace: persistenceModule.workspace,
        migration: migrationModule,
        canvasWorkspace: canvasController,
        nodeWorkspace: nodeController,
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
                    <button class="engine-canvas-select" type="button"
                        data-engine-canvas-action="select"
                        data-canvas-id="${escapeHtml(canvas.id)}">
                        <span>${index + 1}</span>
                        <div>
                            <strong>${escapeHtml(canvas.name || `Lienzo ${index + 1}`)}</strong>
                            <small>${escapeHtml(canvas.type || "PERSONALIZADA")}</small>
                        </div>
                    </button>
                    <div class="engine-canvas-item-actions">
                        <button type="button" data-engine-canvas-action="up" data-canvas-id="${escapeHtml(canvas.id)}">↑</button>
                        <button type="button" data-engine-canvas-action="down" data-canvas-id="${escapeHtml(canvas.id)}">↓</button>
                        <button type="button" data-engine-canvas-action="duplicate" data-canvas-id="${escapeHtml(canvas.id)}">⧉</button>
                        <button type="button" data-engine-canvas-action="visibility" data-canvas-id="${escapeHtml(canvas.id)}">${canvas.visible === false ? "○" : "●"}</button>
                        <button type="button" data-engine-canvas-action="delete" data-canvas-id="${escapeHtml(canvas.id)}">×</button>
                    </div>
                </article>
            `).join("")}
        </div>
    `;
}

function renderSelectedCanvas(node, canvas, assets, selectedNodeId) {
    if (!node) return;
    node.innerHTML = "";
    if (!canvas) {
        node.innerHTML = '<div class="engine-live-empty"><strong>Sin lienzo seleccionado</strong></div>';
        return;
    }
    node.appendChild(renderCanvasPreview(canvas, { assets, selectedNodeId }));
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
