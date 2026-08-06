/**
 * Puente temporal para comandos del historial existente de Builder R3.
 * No depende del DOM: traduce acciones de R3 al contrato del HistoryService.
 */
export function createR3HistoryAdapter(historyService) {
    if (!historyService) throw new TypeError("historyService es obligatorio.");
    return Object.freeze({
        begin(label = "Cambio R3", mergeKey = null) {
            historyService.beginTransaction({ label, mergeKey });
        },
        commit(label) {
            return historyService.commitTransaction({ label });
        },
        cancel() {
            return historyService.cancelTransaction();
        },
        undo() {
            return historyService.undo();
        },
        redo() {
            return historyService.redo();
        },
        canUndo() {
            return historyService.canUndo;
        },
        canRedo() {
            return historyService.canRedo;
        },
        timeline() {
            return historyService.timeline();
        },
    });
}
