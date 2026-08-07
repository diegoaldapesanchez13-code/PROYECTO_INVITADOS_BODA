export const LAYER_COMMANDS = Object.freeze({
    BRING_FORWARD: "BRING_FORWARD",
    SEND_BACKWARD: "SEND_BACKWARD",
    BRING_TO_FRONT: "BRING_TO_FRONT",
    SEND_TO_BACK: "SEND_TO_BACK",
    MOVE_BEFORE: "MOVE_BEFORE",
    MOVE_AFTER: "MOVE_AFTER",
    MOVE_INSIDE: "MOVE_INSIDE",
    TOGGLE_VISIBLE: "TOGGLE_VISIBLE",
    TOGGLE_LOCKED: "TOGGLE_LOCKED",
    RENAME: "RENAME",
    DUPLICATE: "DUPLICATE",
    REMOVE: "REMOVE",
});

export function executeLayerCommand(service, nodes, command, payload = {}) {
    switch (command) {
        case LAYER_COMMANDS.BRING_FORWARD:
            return service.bringForward(nodes, payload.nodeId);
        case LAYER_COMMANDS.SEND_BACKWARD:
            return service.sendBackward(nodes, payload.nodeId);
        case LAYER_COMMANDS.BRING_TO_FRONT:
            return service.bringToFront(nodes, payload.nodeId);
        case LAYER_COMMANDS.SEND_TO_BACK:
            return service.sendToBack(nodes, payload.nodeId);
        case LAYER_COMMANDS.MOVE_BEFORE:
            return service.moveBefore(nodes, payload.nodeId, payload.targetId);
        case LAYER_COMMANDS.MOVE_AFTER:
            return service.moveAfter(nodes, payload.nodeId, payload.targetId);
        case LAYER_COMMANDS.MOVE_INSIDE:
            return service.moveInside(
                nodes,
                payload.nodeId,
                payload.parentId,
                payload.options,
            );
        case LAYER_COMMANDS.TOGGLE_VISIBLE:
            return service.setVisibility(nodes, payload.nodeId, payload.visible);
        case LAYER_COMMANDS.TOGGLE_LOCKED:
            return service.setLocked(nodes, payload.nodeId, payload.locked);
        case LAYER_COMMANDS.RENAME:
            return service.rename(nodes, payload.nodeId, payload.name);
        case LAYER_COMMANDS.DUPLICATE:
            return service.duplicate(nodes, payload.nodeId, payload.options);
        case LAYER_COMMANDS.REMOVE:
            return service.remove(nodes, payload.nodeId, payload.options);
        default:
            throw new Error(`Comando de capa no soportado: ${command}`);
    }
}
