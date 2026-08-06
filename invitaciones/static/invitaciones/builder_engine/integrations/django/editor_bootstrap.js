import { BuilderApp } from "../../app/index.js";
import {
    createDjangoPersistenceAdapter,
    registerPersistenceModule,
} from "../../persistence/index.js";
import { registerMigrationModule } from "../../migration/index.js";

const root = document.querySelector("[data-builder-engine-root]");

if (root) {
    mountBuilderEngine(root).catch((error) => {
        console.error("No fue posible iniciar DIRTEC Builder Engine.", error);
        setStatus(root, "ERROR", error.message || "Error al iniciar el editor.");
    });
}

async function mountBuilderEngine(root) {
    const config = readBootstrap(root);
    const canvasList = root.querySelector("[data-engine-canvases]");
    const documentInfo = root.querySelector("[data-engine-document-info]");
    const migrationNotice = root.querySelector("[data-engine-migration-notice]");
    const saveButton = root.querySelector("[data-engine-action='save']");
    const publishButton = root.querySelector("[data-engine-action='publish']");
    const reloadButton = root.querySelector("[data-engine-action='reload']");

    setStatus(root, "LOADING", "Cargando documento…");

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

    const render = () => {
        const documentValue = app.getDocument();
        renderDocumentInfo(documentInfo, documentValue);
        renderCanvases(canvasList, documentValue.canvases || []);
        root.dataset.dirty = app.isDirty ? "true" : "false";
    };

    app.subscribe((event) => {
        if (
            event.type === "document:changed"
            || event.type === "document:replaced"
            || event.type === "document:saved"
        ) render();
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
        const report = migrationModule.migrateIfNeeded(app);
        if (report.migrated) {
            showMigrationNotice(migrationNotice, report);
            await persistenceModule.service.save({
                reason: "legacy-schema-migration",
            });
        }
    });

    window.DIRTEC_BUILDER = Object.freeze({
        app,
        persistence: persistenceModule.service,
        workspace: persistenceModule.workspace,
        migration: migrationModule,
        config,
    });

    render();
    setStatus(root, "SAVED", "Builder Engine conectado");
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

function renderCanvases(node, canvases) {
    if (!node) return;
    if (!canvases.length) {
        node.innerHTML = `
            <article class="engine-empty">
                <span class="engine-empty-icon">＋</span>
                <h2>Documento vacío</h2>
                <p>Agrega el primer lienzo en el siguiente sprint.</p>
            </article>
        `;
        return;
    }

    node.innerHTML = canvases.map((canvas, index) => `
        <article class="engine-canvas-card">
            <header>
                <span>${index + 1}</span>
                <div>
                    <strong>${escapeHtml(canvas.name || `Lienzo ${index + 1}`)}</strong>
                    <small>${escapeHtml(canvas.type || canvas.id || "")}</small>
                </div>
            </header>
            <div class="engine-canvas-preview">
                <div class="engine-node-summary">
                    ${renderNodeSummary(canvas.nodes || [])}
                </div>
            </div>
        </article>
    `).join("");
}

function renderNodeSummary(nodes) {
    const flat = flattenNodes(nodes);
    if (!flat.length) return "<span>Sin elementos</span>";
    return flat.slice(0, 18).map((node) => `
        <span class="engine-node-chip">
            ${escapeHtml(node.type || "NODE")} · ${escapeHtml(node.name || node.id || "")}
        </span>
    `).join("");
}

function flattenNodes(nodes = []) {
    return nodes.flatMap((node) => [
        node,
        ...flattenNodes(Array.isArray(node.children) ? node.children : []),
    ]);
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
