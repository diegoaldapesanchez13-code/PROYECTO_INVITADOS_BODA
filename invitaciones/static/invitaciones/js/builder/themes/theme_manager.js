import { DEFAULT_THEME_ID } from "./default_theme.js";
import { ThemeRegistry } from "./theme_registry.js";

const clone = (value) => typeof structuredClone === "function"
    ? structuredClone(value)
    : JSON.parse(JSON.stringify(value));

export class ThemeManager {
    #registry;
    #theme;

    constructor({ registry = new ThemeRegistry(), theme = {} } = {}) {
        this.#registry = registry;
        this.#theme = this.resolve(theme);
    }

    resolve(theme = {}) {
        const base = this.#registry.get(theme.id || DEFAULT_THEME_ID)
            || this.#registry.get(DEFAULT_THEME_ID)
            || {};
        return deepMerge(base, theme);
    }

    set(theme) {
        this.#theme = this.resolve(theme);
        return this.current;
    }

    get current() {
        return clone(this.#theme);
    }
}

function deepMerge(base, patch) {
    const result = clone(base || {});
    for (const [key, value] of Object.entries(patch || {})) {
        if (value && typeof value === "object" && !Array.isArray(value)) {
            result[key] = deepMerge(result[key] || {}, value);
        } else {
            result[key] = clone(value);
        }
    }
    return result;
}
