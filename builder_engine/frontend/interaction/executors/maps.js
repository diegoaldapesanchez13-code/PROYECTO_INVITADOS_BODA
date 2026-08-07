export const mapsExecutor = Object.freeze({
    type: "GOOGLE_MAPS",
    validate(action) {
        return String(action.value || action.target || "").trim()
            ? []
            : ["La ubicación de Google Maps es obligatoria."];
    },
    execute(action, context = {}) {
        const location = String(action.value || action.target || "").trim();
        const errors = this.validate(action);
        if (errors.length) throw new Error(errors.join("\n"));
        const url = /^https?:\/\//i.test(location)
            ? location
            : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location)}`;
        return context.navigation?.openUrl
            ? context.navigation.openUrl(url, { newTab: true })
            : { handled: true, type: "GOOGLE_MAPS", url };
    },
});
