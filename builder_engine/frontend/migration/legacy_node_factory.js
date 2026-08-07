export function createLegacyNodeFactory(options = {}) {
    let sequence = 0;
    const idFactory = options.idFactory || ((prefix) => `${prefix}-${++sequence}`);

    function textNode(section, role, text, config = {}) {
        return {
            id: idFactory(`${section.type.toLowerCase()}-${role}`),
            type: "TEXT",
            name: role === "title" ? "Título" : "Descripción",
            visible: role === "title"
                ? config.titleVisible !== false
                : config.textVisible !== false,
            locked: role === "title"
                ? Boolean(config.titleLocked)
                : Boolean(config.textLocked),
            content: {
                text: String(text || ""),
                role,
                legacySectionType: section.type,
            },
            style: {
                x: number(config[`${role}X`], 50),
                y: number(config[`${role}Y`], role === "title" ? 22 : 34),
                width: number(config[`${role}Width`], role === "title" ? 72 : 78),
                scale: number(config[`${role}Scale`], 1),
                rotation: number(config[`${role}Rotation`], 0),
                opacity: number(config[`${role}Opacity`], 1),
                zIndex: number(config[`${role}Z`], 2),
                textAlign: config[`${role}Align`] || config.textAlign || "center",
            },
            children: [],
        };
    }

    function mediaNode(section, role, assetRef, config = {}) {
        if (!assetRef?.url) return null;
        return {
            id: idFactory(`${section.type.toLowerCase()}-${role}`),
            type: assetRef.isVideo ? "VIDEO" : "IMAGE",
            name: role === "background" ? "Fondo" : "Título visual",
            visible: role === "background"
                ? config.showBackgroundLayer !== false
                : config.showTitleAsset !== false,
            locked: false,
            content: {
                assetId: String(assetRef.id || ""),
                url: assetRef.url,
                sourceType: assetRef.isVideo ? "upload" : "image",
                legacySectionType: section.type,
                role,
            },
            style: {
                x: role === "background" ? number(config.backgroundX, 50) : number(config.titleX, 50),
                y: role === "background" ? number(config.backgroundY, 50) : number(config.titleY, 50),
                width: role === "background" ? 100 : number(config.titleWidth, 72),
                scale: role === "background" ? number(config.backgroundScale, 1) : number(config.titleScale, 1),
                opacity: role === "background" ? number(config.backgroundOpacity, 1) : number(config.titleOpacity, 1),
                rotation: role === "background" ? 0 : number(config.titleRotation, 0),
                zIndex: role === "background" ? 0 : number(config.titleZ, 2),
                fit: role === "background" ? config.backgroundFit || "cover" : "contain",
            },
            children: [],
        };
    }

    function customLayerNode(section, layer = {}) {
        const kind = String(layer.kind || "text").toLowerCase();
        const type = kind === "image" ? "IMAGE" : kind === "video" ? "VIDEO" : "TEXT";
        return {
            id: String(layer.id || idFactory(`${section.type.toLowerCase()}-layer`)),
            type,
            name: String(layer.name || "Capa personalizada"),
            visible: layer.visible !== false,
            locked: Boolean(layer.locked),
            content: type === "TEXT"
                ? { text: String(layer.text || ""), legacySectionType: section.type }
                : {
                    assetId: String(layer.asset?.id || ""),
                    url: layer.asset?.url || "",
                    sourceType: type === "VIDEO" ? "upload" : "image",
                    legacySectionType: section.type,
                },
            style: {
                x: number(layer.x, 50),
                y: number(layer.y, 50),
                width: number(layer.width, type === "TEXT" ? 64 : 42),
                scale: number(layer.scale, 1),
                rotation: number(layer.rotation, 0),
                opacity: number(layer.opacity, 1),
                zIndex: number(layer.z, 3),
                textAlign: layer.align || "center",
                fit: layer.fit || "contain",
            },
            children: [],
        };
    }

    function countdownNode(section, config = {}) {
        const labels = [
            ["days", "Días"],
            ["hours", "Horas"],
            ["minutes", "Minutos"],
            ["seconds", "Segundos"],
        ];
        return {
            id: idFactory(`${section.type.toLowerCase()}-countdown`),
            type: "COUNTDOWN",
            name: "Cuenta regresiva",
            visible: true,
            locked: false,
            content: {
                targetDate: config.targetDate || "",
                legacySectionType: section.type,
                migratedComposite: true,
            },
            style: {
                x: number(config.counterX, 50),
                y: number(config.counterY, 68),
                width: number(config.counterWidth, 92),
                scale: number(config.counterScale, 1),
                zIndex: number(config.counterZ, 35),
                layout: config.countdownLayout || "grid",
            },
            children: labels.map(([unit, label]) => ({
                id: idFactory(`countdown-${unit}`),
                type: "CARD",
                name: label,
                visible: true,
                locked: false,
                content: { countdownUnit: unit },
                style: {},
                children: [
                    {
                        id: idFactory(`countdown-${unit}-value`),
                        type: "TEXT",
                        name: `${label} · Número`,
                        visible: true,
                        locked: false,
                        content: {
                            text: "00",
                            binding: { source: "COUNTDOWN", unit, role: "value" },
                        },
                        style: {},
                        children: [],
                    },
                    {
                        id: idFactory(`countdown-${unit}-label`),
                        type: "TEXT",
                        name: `${label} · Etiqueta`,
                        visible: true,
                        locked: false,
                        content: {
                            text: label,
                            binding: { source: "COUNTDOWN", unit, role: "label" },
                        },
                        style: {},
                        children: [],
                    },
                ],
            })),
        };
    }

    function realContentNode(section, config = {}) {
        const real = config.realContent;
        if (!real || real.enabled === false) return null;
        return {
            id: idFactory(`${section.type.toLowerCase()}-real-content`),
            type: "CONTAINER",
            name: "Contenido real",
            visible: true,
            locked: false,
            content: {
                legacySectionType: section.type,
                data: clone(real),
            },
            style: {
                x: number(real.x, 50),
                y: number(real.y, 50),
                width: number(real.width, 100),
                scale: number(real.scale, 1),
                rotation: number(real.rotation, 0),
                opacity: number(real.opacity, 1),
                zIndex: number(real.zIndex, 5),
                gap: number(real.gap, 14),
                direction: real.layout === "stack" ? "column" : "row",
            },
            children: [],
        };
    }

    return Object.freeze({
        textNode,
        mediaNode,
        customLayerNode,
        countdownNode,
        realContentNode,
    });
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
}
function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}
