export const componentEventExecutor = Object.freeze({
    type: "COMPONENT_EVENT",
    validate(action) {
        return String(action.target || action.value || "").trim()
            ? []
            : ["El nombre del evento del componente es obligatorio."];
    },
    execute(action, context = {}) {
        const eventName = String(action.target || action.value || "").trim();
        const errors = this.validate(action);
        if (errors.length) throw new Error(errors.join("\n"));
        const payload = action.payload || {};
        if (typeof context.emitComponentEvent === "function") {
            return context.emitComponentEvent(eventName, payload);
        }
        return { handled: true, type: "COMPONENT_EVENT", eventName, payload };
    },
});
