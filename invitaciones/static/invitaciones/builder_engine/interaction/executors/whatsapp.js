export const whatsappExecutor = Object.freeze({
    type: "WHATSAPP",
    validate(action) {
        const phone = normalizePhone(action.target || action.value);
        return phone ? [] : ["El número de WhatsApp es obligatorio."];
    },
    execute(action, context = {}) {
        const phone = normalizePhone(action.target || action.value);
        const errors = this.validate(action);
        if (errors.length) throw new Error(errors.join("\n"));
        const message = String(action.payload?.message || action.value || "");
        const url = `https://wa.me/${phone}${message ? `?text=${encodeURIComponent(message)}` : ""}`;
        return context.navigation?.openUrl
            ? context.navigation.openUrl(url, { newTab: true })
            : { handled: true, type: "WHATSAPP", url };
    },
});

function normalizePhone(value) {
    return String(value || "").replace(/[^\d]/g, "");
}
