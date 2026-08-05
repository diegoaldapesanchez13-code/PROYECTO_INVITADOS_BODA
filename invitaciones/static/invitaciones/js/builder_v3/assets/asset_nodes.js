
import {
    COORDINATE_SPACES,
    LAYOUT_MODES,
    NODE_TYPES,
    isContainerComponent,
} from "../core/index.js";

import {
    ASSET_TYPES,
} from "./asset_manager.js";



export function useAsset({
    state,
    asset,
    selectedNodeId = null,
    position = null,
}) {
    if (!state || !asset) {
        throw new Error(
            "useAsset requiere state y asset."
        );
    }

    const target = resolveTarget(
        state,
        selectedNodeId
    );

    if (!target) {
        throw new Error(
            "No existe una sección o contenedor destino."
        );
    }

    if (
        asset.type === ASSET_TYPES.BACKGROUND
        || asset.type === ASSET_TYPES.TEXTURE
    ) {
        return applyBackgroundAsset(
            state,
            target,
            asset
        );
    }

    if (
        asset.type === ASSET_TYPES.DECORATION
        || asset.type === ASSET_TYPES.ICON
    ) {
        return createDecorationNode(
            state,
            target,
            asset,
            position
        );
    }

    if (asset.type === ASSET_TYPES.IMAGE) {
        return createImageNode(
            state,
            target,
            asset,
            position
        );
    }

    throw new Error(
        `Tipo de asset no soportado: ${asset.type}`
    );
}

export function resolveTarget(
    state,
    selectedNodeId
) {
    let current = selectedNodeId
        ? state.getNode(selectedNodeId)
        : null;

    while (current) {
        if (isContainerComponent(current.type)) {
            return current;
        }

        current = current.parentId
            ? state.getNode(current.parentId)
            : null;
    }

    return state.document.sections[0] || null;
}

function applyBackgroundAsset(
    state,
    target,
    asset
) {
    const children =
        state.getChildren(target.id);

    const existing =
        children.find(
            (node) =>
                node.type
                === NODE_TYPES.BACKGROUND
        );

    const patch = {
        content: {
            assetId: asset.id,
            src: asset.url,
        },
        style: {
            ...(existing?.style || {}),
            fit: "cover",
            positionX: 50,
            positionY: 50,
            zoom: 1,
            brightness: 1,
            contrast: 1,
            saturation: 1,
            blur: 0,
        },
        opacity: 1,
    };

    if (existing) {
        return state.updateNode(
            existing.id,
            patch,
            {
                ignoreLock: true,
            }
        );
    }

    return state.createNode(
        NODE_TYPES.BACKGROUND,
        {
            name:
                `Fondo · ${asset.name}`,
            parentId: target.id,
            sectionId:
                target.type === NODE_TYPES.SECTION
                    ? target.id
                    : target.sectionId,
            layoutMode:
                LAYOUT_MODES.LAYER,
            coordinateSpace:
                target.type === NODE_TYPES.SECTION
                    ? COORDINATE_SPACES.SECTION
                    : COORDINATE_SPACES.PARENT,
            x: 50,
            y: 50,
            width: 100,
            height: 100,
            zIndex: 0,
            ...patch,
        }
    );
}

function createDecorationNode(
    state,
    target,
    asset,
    position
) {
    return state.createNode(
        NODE_TYPES.DECORATION,
        {
            name: asset.name,
            parentId: target.id,
            sectionId:
                target.type === NODE_TYPES.SECTION
                    ? target.id
                    : target.sectionId,
            layoutMode:
                LAYOUT_MODES.ABSOLUTE,
            coordinateSpace:
                target.type === NODE_TYPES.SECTION
                    ? COORDINATE_SPACES.SECTION
                    : COORDINATE_SPACES.PARENT,
            x:
                Number(position?.x ?? 50),
            y:
                Number(position?.y ?? 50),
            width: 32,
            height: 32,
            zIndex: 30,
            content: {
                assetId: asset.id,
                src: asset.url,
                alt: asset.name,
            },
            style: {
                objectFit: "contain",
                objectPosition: "center",
                flipX: false,
                flipY: false,
                brightness: 1,
                contrast: 1,
                saturation: 1,
                blur: 0,
            },
        }
    );
}

function createImageNode(
    state,
    target,
    asset,
    position
) {
    return state.createNode(
        NODE_TYPES.IMAGE,
        {
            name: asset.name,
            parentId: target.id,
            sectionId:
                target.type === NODE_TYPES.SECTION
                    ? target.id
                    : target.sectionId,
            layoutMode:
                LAYOUT_MODES.ABSOLUTE,
            coordinateSpace:
                target.type === NODE_TYPES.SECTION
                    ? COORDINATE_SPACES.SECTION
                    : COORDINATE_SPACES.PARENT,
            x:
                Number(position?.x ?? 50),
            y:
                Number(position?.y ?? 50),
            width: 56,
            height: 34,
            zIndex: 20,
            content: {
                assetId: asset.id,
                src: asset.url,
                alt: asset.name,
            },
            style: {
                objectFit: "cover",
                objectPosition: "center",
                borderRadius: 18,
                brightness: 1,
                contrast: 1,
                saturation: 1,
                blur: 0,
            },
        }
    );
}
