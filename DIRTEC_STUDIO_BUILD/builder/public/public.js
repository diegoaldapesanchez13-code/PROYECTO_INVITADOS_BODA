import { UniversalRenderer } from "../renderer/renderer.js";
import { ExperienceController } from "../experience/controller.js";

function readBootstrap() {
    const node = document.getElementById("dirtec-builder-public-bootstrap");
    if (!node) throw new Error("Bootstrap público no disponible.");
    return JSON.parse(node.textContent || "{}");
}

function cookie(name) {
    const prefix = `${name}=`;
    return document.cookie.split(";").map(v => v.trim()).find(v => v.startsWith(prefix))?.slice(prefix.length) || "";
}

function createAssetResolver(items = []) {
    const map = new Map(items.map(asset => [String(asset.id), asset]));
    return (assetId) => {
        const asset = map.get(String(assetId));
        return asset?.url || asset?.previewUrl || "";
    };
}

function createAssetLookup(items = []) {
    const map = new Map(items.map(asset => [String(asset.id), asset]));
    return (assetId) => map.get(String(assetId)) || null;
}

function createRsvpProvider(bootstrap) {
    const endpoint = bootstrap.endpoints?.rsvp;
    return {
        async load() {
            const response = await fetch(endpoint, {
                credentials: "same-origin",
                cache: "no-store",
                headers: { Accept: "application/json" },
            });
            const payload = await response.json();
            if (!response.ok || !payload.ok) throw new Error(payload.error || "No fue posible cargar RSVP.");
            return payload.data;
        },
        async submit(data) {
            const response = await fetch(endpoint, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                    "X-CSRFToken": decodeURIComponent(cookie("csrftoken")),
                },
                body: JSON.stringify(data),
            });
            const payload = await response.json();
            if (!response.ok || !payload.ok) throw new Error(payload.error || "No fue posible guardar RSVP.");
            return payload;
        },
    };
}

const bootstrap = readBootstrap();
const root = document.getElementById("dirtec-public-root");
const assetItems =
    Array.isArray(bootstrap.assets) && bootstrap.assets.length
        ? bootstrap.assets
        : bootstrap.document?.assets || [];
const assetResolver = createAssetResolver(assetItems);
const assetLookup = createAssetLookup(assetItems);
const renderer = new UniversalRenderer({
    editable: false,
    device: bootstrap.device || "mobile",
    assetResolver,
    invitationContext: {
        ...(bootstrap.invitation || {}),
        invitationId:
            bootstrap.invitation?.invitationId,
        pathname: location.pathname,
    },
    eventContext: bootstrap.event || {},
    rsvpProvider: createRsvpProvider(bootstrap),
    onInteractionError(error) { console.error("DIRTEC interaction", error); },
    onRsvpError(error) { console.error("DIRTEC RSVP", error); },
});

const experience = new ExperienceController({
    document: bootstrap.document,
    root: document.body,
    invitationElement: root,
    assetResolver: assetLookup,
    logger: console,
    renderInvitation() {
        renderer.mount(root, bootstrap.document);
    },
});

experience.start();
globalThis.__DIRTEC_PUBLIC_RENDERER__ = renderer;
globalThis.__DIRTEC_PUBLIC_EXPERIENCE__ = experience;
