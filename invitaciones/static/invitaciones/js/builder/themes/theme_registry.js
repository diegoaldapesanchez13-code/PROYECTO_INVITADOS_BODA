import { DEFAULT_THEME, DEFAULT_THEME_ID } from "./default_theme.js";

const clone = (value) => typeof structuredClone === "function"
    ? structuredClone(value)
    : JSON.parse(JSON.stringify(value));

export class ThemeRegistry {
    #themes = new Map();

    constructor(themes = [DEFAULT_THEME]) {
        for (const theme of themes) {
            this.register(theme);
        }
    }

    register(theme) {
        if (!theme || typeof theme !== "object" || !theme.id) {
            throw new TypeError("El tema debe incluir un id.");
        }
        this.#themes.set(String(theme.id), clone(theme));
        return this.get(theme.id);
    }

    get(themeId = DEFAULT_THEME_ID) {
        const theme = this.#themes.get(String(themeId));
        return theme ? clone(theme) : null;
    }

    has(themeId) {
        return this.#themes.has(String(themeId));
    }

    list() {
        return [...this.#themes.values()].map(clone);
    }
}
