function clone(value) {
    if (typeof structuredClone === "function") return structuredClone(value);
    return JSON.parse(JSON.stringify(value));
}

export function getPath(source, path, fallback = undefined) {
    const segments = normalizePath(path);
    let current = source;
    for (const segment of segments) {
        if (current == null || !Object.prototype.hasOwnProperty.call(current, segment)) {
            return fallback;
        }
        current = current[segment];
    }
    return current;
}

export function setPathClone(source, path, value) {
    const segments = normalizePath(path);
    if (!segments.length) return clone(value);
    const result = source && typeof source === "object" ? clone(source) : {};
    let cursor = result;
    segments.forEach((segment, index) => {
        if (index === segments.length - 1) {
            cursor[segment] = clone(value);
            return;
        }
        const next = cursor[segment];
        cursor[segment] = next && typeof next === "object" && !Array.isArray(next)
            ? clone(next)
            : {};
        cursor = cursor[segment];
    });
    return result;
}

export function normalizePath(path) {
    if (Array.isArray(path)) return path.map(String).filter(Boolean);
    return String(path || "")
        .replace(/\[(\w+)\]/g, ".$1")
        .split(".")
        .map((part) => part.trim())
        .filter(Boolean);
}
