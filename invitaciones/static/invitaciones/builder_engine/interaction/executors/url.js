export const urlExecutor = Object.freeze({
    type: "URL",
    validate(action) {
        return isSafeUrl(action.value) ? [] : ["La URL no es válida o segura."];
    },
    execute(action, context = {}) {
        const url = String(action.value || "").trim();
        const errors = this.validate(action);
        if (errors.length) throw new Error(errors.join("\n"));
        return context.navigation?.openUrl
            ? context.navigation.openUrl(url, { newTab: action.openInNewTab })
            : { handled: true, type: "URL", url, newTab: action.openInNewTab };
    },
});

function isSafeUrl(value) {
    const url = String(value || "").trim();
    if (!url) return false;
    if (url.startsWith("#") || url.startsWith("/")) return true;
    try {
        const parsed = new URL(url);
        return ["http:", "https:", "mailto:", "tel:"].includes(parsed.protocol);
    } catch {
        return false;
    }
}
