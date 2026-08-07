export const DEFAULT_THEME_ID = "dirtec-default";

export const DEFAULT_THEME = Object.freeze({
    id: DEFAULT_THEME_ID,
    name: "DIRTEC Default",
    version: 1,
    colors: {
        background: "#ffffff",
        surface: "#f7f7f7",
        text: "#1f2937",
        muted: "#6b7280",
        primary: "#445c3c",
        accent: "#c7a96b",
    },
    typography: {
        heading: "Playfair Display",
        body: "Inter",
    },
    radius: {
        small: 8,
        medium: 16,
        large: 28,
    },
});
