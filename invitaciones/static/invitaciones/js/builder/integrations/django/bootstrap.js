import { BuilderApp } from "../../app/builder_app.js";
import { DjangoEndpoints } from "./endpoints.js";
import { DjangoDocumentAdapter } from "./adapters/document_adapter.js";
import { DjangoAssetAdapter } from "./adapters/asset_adapter.js";

export function readDjangoBuilderConfig({
    configElementId = "builder-r3-config",
    documentElementId = "builder-r3-document",
    assetsElementId = "builder-r3-assets",
} = {}) {
    return {
        config: readJsonScript(configElementId, {}),
        document: readJsonScript(documentElementId, {}),
        assets: readJsonScript(assetsElementId, []),
    };
}

export async function bootstrapDjangoBuilder(options = {}) {
    const injected = options.injected || readDjangoBuilderConfig(options);
    const config = { ...(injected.config || {}), ...(options.config || {}) };
    const documentAdapter = options.documentAdapter || new DjangoDocumentAdapter();
    const assetAdapter = options.assetAdapter || new DjangoAssetAdapter();
    const endpoints = options.endpoints || new DjangoEndpoints({
        urls: config.urls || {},
        csrfToken: config.csrfToken || getCookie("csrftoken"),
        fetchImpl: options.fetchImpl,
    });

    return BuilderApp.start({
        backend: "django",
        eventId: config.eventId ?? null,
        document: documentAdapter.fromBackend(injected.document),
        assets: assetAdapter.listFromBackend(injected.assets),
        endpoints,
        documentAdapter,
        createRuntime: options.createRuntime,
        root: options.root,
    });
}

function readJsonScript(id, fallback) {
    const element = globalThis.document?.getElementById(id);
    if (!element) return fallback;
    try {
        return JSON.parse(element.textContent || "");
    } catch (error) {
        console.error(`JSON inválido en #${id}`, error);
        return fallback;
    }
}

function getCookie(name) {
    const cookie = globalThis.document?.cookie || "";
    const item = cookie.split(";").map((value) => value.trim())
        .find((value) => value.startsWith(`${name}=`));
    return item ? decodeURIComponent(item.slice(name.length + 1)) : "";
}
