export function validatePersistencePort(port = {}) {
    const errors = [];
    for (const method of ["load", "save", "publish"]) {
        if (typeof port[method] !== "function") {
            errors.push(`PersistencePort requiere ${method}().`);
        }
    }
    return { valid: errors.length === 0, errors };
}

export function requirePersistencePort(port) {
    const result = validatePersistencePort(port);
    if (!result.valid) throw new TypeError(result.errors.join("\n"));
    return port;
}
