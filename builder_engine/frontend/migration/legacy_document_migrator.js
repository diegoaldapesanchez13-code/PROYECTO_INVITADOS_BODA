import {
    LEGACY_EDITOR_FORMAT,
    MIGRATOR_VERSION,
    TARGET_SCHEMA_VERSION,
} from "./constants.js";
import { collectLegacyAssets } from "./legacy_asset_collector.js";
import { createLegacyNodeFactory } from "./legacy_node_factory.js";

export function isLegacyMigrationPending(document) {
    return Boolean(
        document
        && document.schemaVersion === TARGET_SCHEMA_VERSION
        && document.globals?.legacyMigrationPending
        && document.globals?.legacyEditorConfig
        && (!Array.isArray(document.canvases) || document.canvases.length === 0)
    );
}

export function migrateLegacyDocument(document, options = {}) {
    if (!isLegacyMigrationPending(document)) {
        return {
            migrated: false,
            document: clone(document),
            report: {
                reason: "not-pending",
                canvases: 0,
                nodes: 0,
                assets: 0,
            },
        };
    }

    const next = clone(document);
    const legacy = next.globals.legacyEditorConfig || {};
    const factory = createLegacyNodeFactory(options);
    const sections = Array.isArray(legacy.sections) ? [...legacy.sections] : [];
    sections.sort((a, b) => Number(a.order || 0) - Number(b.order || 0));

    const canvases = sections.map((section, index) => migrateSection(
        section,
        index,
        factory,
        options,
    ));

    const collectedAssets = collectLegacyAssets(legacy);
    next.assets = mergeAssets(next.assets || [], collectedAssets);
    next.theme = {
        ...(legacy.theme && typeof legacy.theme === "object" ? legacy.theme : {}),
        ...(next.theme || {}),
    };
    next.canvases = canvases;
    next.globals = {
        ...(legacy.layout && typeof legacy.layout === "object"
            ? { legacyLayout: clone(legacy.layout) }
            : {}),
        ...next.globals,
        legacyMigrationPending: false,
        legacyMigration: {
            sourceFormat: LEGACY_EDITOR_FORMAT,
            migratorVersion: MIGRATOR_VERSION,
            migratedAt: new Date().toISOString(),
            sourceSectionCount: sections.length,
        },
    };
    delete next.globals.legacyEditorConfig;

    next.documentVersion = Number(next.documentVersion || 1) + 1;
    if (next.metadata) {
        next.metadata.updatedAt = new Date().toISOString();
    }

    return {
        migrated: true,
        document: next,
        report: {
            reason: "migrated",
            canvases: canvases.length,
            nodes: canvases.reduce(
                (total, canvas) => total + countNodes(canvas.nodes),
                0,
            ),
            assets: collectedAssets.length,
        },
    };
}

function migrateSection(section = {}, index, factory, options) {
    const config = section.config && typeof section.config === "object"
        ? section.config
        : {};
    const type = String(section.type || "PERSONALIZADA").toUpperCase();
    const normalizedSection = { ...section, type };
    const nodes = [];

    const background = factory.mediaNode(
        normalizedSection,
        "background",
        config.backgroundAsset,
        config,
    );
    if (background) nodes.push(background);

    const titleAsset = factory.mediaNode(
        normalizedSection,
        "titleAsset",
        config.titleAsset,
        config,
    );
    if (titleAsset) nodes.push(titleAsset);

    if (section.title && config.showTextTitle !== false) {
        nodes.push(factory.textNode(
            normalizedSection,
            "title",
            section.title,
            config,
        ));
    }

    if (section.description) {
        nodes.push(factory.textNode(
            normalizedSection,
            "text",
            section.description,
            config,
        ));
    }

    if (type === "CUENTA_REGRESIVA") {
        nodes.push(factory.countdownNode(normalizedSection, config));
    }

    const realContent = factory.realContentNode(normalizedSection, config);
    if (realContent) nodes.push(realContent);

    for (const layer of Array.isArray(config.customLayers)
        ? config.customLayers
        : []) {
        nodes.push(factory.customLayerNode(normalizedSection, layer));
    }

    return {
        id: String(section.id || `canvas-${index + 1}`),
        name: String(section.title || labelForType(type)),
        type,
        visible: section.visible !== false,
        locked: false,
        order: Number(section.order || (index + 1) * 10),
        height: Number(config.sectionHeight || 700),
        background: {
            color: config.backgroundColor || "",
            opacity: Number(config.backgroundOpacity ?? 1),
        },
        metadata: {
            sectionId: section.sectionId ?? null,
            legacySectionType: type,
            migratedFromLegacy: true,
        },
        nodes,
    };
}

function mergeAssets(current, incoming) {
    const result = new Map();
    for (const asset of [...current, ...incoming]) {
        if (!asset?.id) continue;
        result.set(String(asset.id), asset);
    }
    return [...result.values()];
}

function countNodes(nodes = []) {
    return nodes.reduce(
        (total, node) => total + 1 + countNodes(node.children || []),
        0,
    );
}

function labelForType(type) {
    return {
        PORTADA: "Portada",
        PADRES_PADRINOS: "Padres y padrinos",
        CUENTA_REGRESIVA: "Cuenta regresiva",
        DETALLES: "Detalles",
        DRESS_CODE: "Dress code",
        ITINERARIO: "Itinerario",
        ALBUM: "Álbum",
        MENU: "Menú",
        REGALOS: "Regalos",
        ALBUM_COMPARTIDO: "Álbum compartido",
        RSVP: "Confirmación",
    }[type] || "Sección";
}

function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
