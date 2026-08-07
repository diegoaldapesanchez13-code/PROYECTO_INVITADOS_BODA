
import { TRANSFORM_HANDLES } from "./transform_session.js";

export function createSelectionOverlay(node, options = {}) {
    if (!node?.id) return null;
    const locked = Boolean(node.locked);
    return {
        nodeId: node.id,
        locked,
        handles: locked ? [] : TRANSFORM_HANDLES.map(position => ({
            id: `resize-${position}`,
            operation: "RESIZE",
            position,
        })),
        rotationHandle: locked ? null : {
            id: "rotate",
            operation: "ROTATE",
        },
        moveEnabled: !locked,
        frame: {
            x: Number(options.frame?.x ?? node.layout?.transform?.x ?? 0),
            y: Number(options.frame?.y ?? node.layout?.transform?.y ?? 0),
            width: Number(options.frame?.width ?? node.layout?.transform?.width ?? 0),
            height: Number(options.frame?.height ?? node.layout?.transform?.height ?? 0),
            rotation: Number(options.frame?.rotation ?? node.layout?.transform?.rotation ?? 0),
        },
    };
}
