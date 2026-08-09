import {
    COORDINATE_SPACES,
    LAYOUT_MODES,
    NODE_TYPES,
    createEmptyDocument,
    createNode,
    normalizeDocument,
} from "./schema.js";

export function migrateLegacyConfig(
    legacyConfig = {},
    options = {}
) {
    const document = createEmptyDocument({
        page: {
            name:
                options.pageName
                || legacyConfig.name
                || "Invitación migrada",
        },
        meta: {
            source: "legacy",
            migratedAt: new Date().toISOString(),
        },
    });

    const legacySections = Array.isArray(
        legacyConfig.sections
    )
        ? legacyConfig.sections
        : [];

    for (const legacySection of legacySections) {
        const section = createLegacySection(
            legacySection
        );

        document.canvases.push(section);

        const background = createLegacyBackground(
            legacySection,
            section.id
        );

        if (background) {
            document.nodes.push(background);
            section.children.push(background.id);
        }

        const contentContainer = createNode(
            NODE_TYPES.CONTAINER,
            {
                name: "Contenido",
                parentId: section.id,
                canvasId: section.id,
                order: section.children.length,
                layoutMode: LAYOUT_MODES.FLOW,
                coordinateSpace:
                    COORDINATE_SPACES.PARENT,
                width:
                    number(
                        legacySection.config
                            ?.layoutContentWidth,
                        100
                    ),
                height: "auto",
                style: {
                    direction:
                        mapDirection(
                            legacySection.config
                                ?.autoLayoutMode
                        ),
                    align:
                        legacySection.config
                            ?.layoutAlignment
                        || "center",
                    justify:
                        legacySection.config
                            ?.layoutJustify
                        || "center",
                    gap:
                        number(
                            legacySection.config
                                ?.layoutSpacing,
                            18
                        ),
                    maxWidth:
                        number(
                            legacySection.config
                                ?.layoutContentMaxWidth,
                            1060
                        ),
                },
            }
        );

        document.nodes.push(contentContainer);
        section.children.push(contentContainer.id);

        if (
            legacySection.type === "CUENTA_REGRESIVA"
        ) {
            const countdown = createLegacyCountdown(
                legacySection,
                section.id,
                contentContainer.id
            );

            document.nodes.push(countdown);
            contentContainer.children.push(
                countdown.id
            );
        }
    }

    const legacyComponents = Array.isArray(
        options.components
    )
        ? options.components
        : [];

    migrateLegacyComponents(
        document,
        legacyComponents
    );

    return normalizeDocument(document);
}

function createLegacySection(legacySection) {
    const config = legacySection.config || {};

    return createNode(NODE_TYPES.CANVAS, {
        id:
            legacySection.r3Id
            || `section-${legacySection.id || legacySection.type}`,
        name:
            legacySection.title
            || legacySection.type
            || "Sección",
        order: number(legacySection.order, 0),
        visible: legacySection.visible !== false,
        canvasId:
            legacySection.r3Id
            || `section-${legacySection.id || legacySection.type}`,
        layoutMode: LAYOUT_MODES.FLOW,
        coordinateSpace:
            COORDINATE_SPACES.CANVAS,
        width: 100,
        height:
            config.layoutAutoHeight
                ? "auto"
                : number(config.sectionHeight, 520),
        minHeight:
            number(config.layoutMinHeight, 0),
        maxHeight:
            number(config.layoutMaxHeight, 0),
        style: {
            paddingX:
                number(config.layoutPaddingX, 20),
            paddingY:
                number(config.layoutPaddingY, 24),
            overflow:
                config.layoutOverflow || "visible",
            textAlign:
                config.textAlign || "center",
        },
        content: {
            legacyType: legacySection.type,
            legacySectionId:
                legacySection.sectionId
                ?? legacySection.id
                ?? null,
            title:
                legacySection.title || "",
            description:
                legacySection.description || "",
        },
    });
}

function createLegacyBackground(
    legacySection,
    sectionId
) {
    const config = legacySection.config || {};
    const backgroundAsset =
        config.backgroundAsset
        || legacySection.backgroundAsset
        || null;

    const backgroundColor =
        config.backgroundColor
        || legacySection.backgroundColor
        || null;

    if (!backgroundAsset && !backgroundColor) {
        return null;
    }

    return createNode(NODE_TYPES.BACKGROUND, {
        name: "Fondo",
        parentId: sectionId,
        canvasId: sectionId,
        order: 0,
        layoutMode: LAYOUT_MODES.LAYER,
        coordinateSpace:
            COORDINATE_SPACES.CANVAS,
        x: number(config.backgroundX, 50),
        y: number(config.backgroundY, 50),
        width: 100,
        height: 100,
        scale: number(config.backgroundScale, 1),
        opacity:
            number(config.backgroundOpacity, 1),
        zIndex: 0,
        style: {
            fit: config.backgroundFit || "cover",
            repeat:
                config.backgroundRepeat
                || "no-repeat",
            brightness:
                number(
                    config.backgroundBrightness,
                    1
                ),
            blur:
                number(config.backgroundBlur, 0),
            color: backgroundColor,
        },
        content: {
            asset: backgroundAsset,
        },
    });
}

function createLegacyCountdown(
    legacySection,
    sectionId,
    parentId
) {
    const config = legacySection.config || {};

    return createNode(NODE_TYPES.COUNTDOWN, {
        name: "Contador",
        parentId,
        canvasId: sectionId,
        order: 0,
        layoutMode:
            config.counterLayoutMode
            || LAYOUT_MODES.ABSOLUTE,
        coordinateSpace:
            COORDINATE_SPACES.PARENT,
        x: number(config.counterX, 50),
        y: number(config.counterY, 68),
        width: number(config.counterWidth, 92),
        height: "auto",
        scale: number(config.counterScale, 1),
        zIndex: number(config.counterZ, 35),
        style: {
            columns: 4,
            gap:
                number(
                    config.layoutSpacing,
                    18
                ),
        },
        content: {
            labels: [
                "Días",
                "Horas",
                "Minutos",
                "Segundos",
            ],
        },
    });
}

function migrateLegacyComponents(
    document,
    components
) {
    const sectionByLegacyId = new Map();

    for (const section of document.canvases) {
        sectionByLegacyId.set(
            String(
                section.content
                    ?.legacySectionId
            ),
            section
        );
    }

    for (const component of components) {
        const section = sectionByLegacyId.get(
            String(component.sectionId)
        );

        if (!section) continue;

        const type = mapLegacyComponentType(
            component.tipo || component.type
        );

        const node = createNode(type, {
            id:
                component.r3Id
                || `component-${component.id}`,
            name:
                component.name
                || component.properties?.label
                || type,
            parentId: section.id,
            canvasId: section.id,
            order: section.children.length,
            visible: component.hidden !== true,
            locked: Boolean(component.locked),
            layoutMode:
                component.layoutMode
                || LAYOUT_MODES.ABSOLUTE,
            coordinateSpace:
                component.coordinateSpace
                || COORDINATE_SPACES.CANVAS,
            x: number(component.x, 50),
            y: number(component.y, 50),
            width: number(component.width, 40),
            height:
                component.height === "auto"
                    ? "auto"
                    : number(component.height, 10),
            rotation:
                number(component.rotation, 0),
            opacity:
                number(component.opacity, 1),
            zIndex:
                number(component.zIndex, 20),
            content:
                component.properties || {},
        });

        document.nodes.push(node);
        section.children.push(node.id);
    }
}

function mapLegacyComponentType(type) {
    const normalized = String(type || "")
        .toUpperCase();

    const map = {
        TEXTO: NODE_TYPES.TEXT,
        TEXT: NODE_TYPES.TEXT,
        IMAGEN: NODE_TYPES.IMAGE,
        IMAGE: NODE_TYPES.IMAGE,
        BOTON: NODE_TYPES.BUTTON,
        BUTTON: NODE_TYPES.BUTTON,
    };

    return map[normalized] || NODE_TYPES.CONTAINER;
}

function mapDirection(value) {
    if (value === "horizontal") return "row";
    if (value === "grid") return "grid";
    return "column";
}

function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed)
        ? parsed
        : fallback;
}