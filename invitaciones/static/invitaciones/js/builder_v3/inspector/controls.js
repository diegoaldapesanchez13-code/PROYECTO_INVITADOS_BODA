export function field({
    key,
    label,
    type = "text",
    path = key,
    min = null,
    max = null,
    step = null,
    unit = "",
    options = [],
    placeholder = "",
    help = "",
    visibleWhen = null,
}) {
    return {
        kind: "field",
        key,
        label,
        type,
        path,
        min,
        max,
        step,
        unit,
        options,
        placeholder,
        help,
        visibleWhen,
    };
}

export function group({
    id,
    title,
    description = "",
    fields = [],
    open = true,
    visibleWhen = null,
}) {
    return {
        kind: "group",
        id,
        title,
        description,
        fields,
        open,
        visibleWhen,
    };
}

export function action({
    id,
    label,
    tone = "default",
    handler,
    visibleWhen = null,
}) {
    return {
        kind: "action",
        id,
        label,
        tone,
        handler,
        visibleWhen,
    };
}

export function actionGroup({
    id,
    title,
    actions = [],
    visibleWhen = null,
}) {
    return {
        kind: "action-group",
        id,
        title,
        actions,
        visibleWhen,
    };
}

export function getPath(object, path, fallback = "") {
    if (!path) return fallback;

    const value = String(path)
        .split(".")
        .reduce(
            (current, key) =>
                current?.[key],
            object
        );

    return value === undefined
        ? fallback
        : value;
}

export function setPathClone(object, path, value) {
    const clone = structuredCloneSafe(object);
    const parts = String(path).split(".");
    let current = clone;

    parts.forEach((part, index) => {
        const last = index === parts.length - 1;

        if (last) {
            current[part] = value;
            return;
        }

        if (
            !current[part]
            || typeof current[part] !== "object"
            || Array.isArray(current[part])
        ) {
            current[part] = {};
        }

        current = current[part];
    });

    return clone;
}

export function valueFromInput(input, definition) {
    if (definition.type === "checkbox") {
        return input.checked;
    }

    if (
        definition.type === "number"
        || definition.type === "range"
    ) {
        const number = Number(input.value);

        return Number.isFinite(number)
            ? number
            : 0;
    }

    return input.value;
}

export function shouldShow(definition, context) {
    return typeof definition.visibleWhen !== "function"
        || definition.visibleWhen(context);
}

function structuredCloneSafe(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return JSON.parse(JSON.stringify(value));
}