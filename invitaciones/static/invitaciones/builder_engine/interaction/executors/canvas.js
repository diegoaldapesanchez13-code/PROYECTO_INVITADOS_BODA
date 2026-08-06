export const canvasExecutor = Object.freeze({
    type: "CANVAS",
    validate(action, context = {}) {
        const target = String(action.target || action.value || "");
        if (!target) return ["El lienzo destino es obligatorio."];
        if (context.document?.canvases && !context.document.canvases.some((canvas) => canvas.id === target)) {
            return [`El lienzo destino no existe: ${target}`];
        }
        return [];
    },
    execute(action, context = {}) {
        const target = String(action.target || action.value || "");
        const errors = this.validate(action, context);
        if (errors.length) throw new Error(errors.join("\n"));
        return context.navigation?.goToCanvas
            ? context.navigation.goToCanvas(target)
            : { handled: true, type: "CANVAS", target };
    },
});
