import {
    EXPERIENCE_AUDIO_START_POLICIES,
    EXPERIENCE_INTRO_MODES,
    normalizeExperience,
} from "./contract.js";

const MODE_LABELS = {
    NONE: "Sin introducción",
    ENVELOPE: "Sobre",
    IMAGE: "Imagen",
    GIF: "GIF",
    VIDEO: "Video",
};

const POLICY_LABELS = {
    MANUAL: "Manual",
    ON_OPEN_GESTURE: "Al abrir",
    AFTER_INTRO: "Después de entrada",
};

const EXPERIENCE_PREVIEW_DEVICES = Object.freeze({
    iphone_13: {
        label: "iPhone 13 / 14",
        width: 390,
        height: 844,
    },
    iphone_se: {
        label: "iPhone SE",
        width: 375,
        height: 667,
    },
    android: {
        label: "Android",
        width: 412,
        height: 915,
    },
});

const MEDIA_POSITION_PRESETS = Object.freeze([
    { x: 0, y: 0, symbol: "↖", label: "Superior izquierda" },
    { x: 50, y: 0, symbol: "↑", label: "Superior" },
    { x: 100, y: 0, symbol: "↗", label: "Superior derecha" },
    { x: 0, y: 50, symbol: "←", label: "Izquierda" },
    { x: 50, y: 50, symbol: "●", label: "Centro" },
    { x: 100, y: 50, symbol: "→", label: "Derecha" },
    { x: 0, y: 100, symbol: "↙", label: "Inferior izquierda" },
    { x: 50, y: 100, symbol: "↓", label: "Inferior" },
    { x: 100, y: 100, symbol: "↘", label: "Inferior derecha" },
]);

export class ExperiencePanel {
    constructor(options = {}) {
        const {
            root,
            state,
            assets,
            onPreview = null,
            onResetPreview = null,
            onStatus = null,
        } = options;

        if (!(root instanceof Element)) {
            throw new TypeError(
                "ExperiencePanel root debe ser un elemento HTML."
            );
        }

        if (!state || typeof state.updateExperience !== "function") {
            throw new Error(
                "ExperiencePanel requiere BuilderState con updateExperience."
            );
        }

        this.root = root;
        this.state = state;
        this.assets = assets;
        this.onPreview = onPreview;
        this.onResetPreview = onResetPreview;
        this.onStatus = onStatus;
        this.previewDeviceKey = "iphone_13";
        this.suppressNextExperienceRender = false;

        this.unsubscribe = this.state.subscribe((event) => {
            if (event.type !== "experience:update") {
                return;
            }

            if (this.suppressNextExperienceRender) {
                this.suppressNextExperienceRender = false;
                return;
            }

            this.render();
        });

        this.render();
    }

    destroy() {
        this.unsubscribe?.();
        this.root.replaceChildren();
    }

    render() {
        const experience = normalizeExperience(
            this.state.document.experience,
        );
        const mode = experience.intro.mode;

        this.root.replaceChildren();
        this.root.classList.add("experience-panel");

        this.root.append(
            this.#header(),
            this.#entrySection(experience, mode),
            this.#musicSection(experience),
            this.#actions(),
        );
    }

    #header() {
        const header = document.createElement("header");
        header.className = "experience-panel__header";
        header.innerHTML = `
            <strong>Experiencia</strong>
            <small>Entrada y música global de la invitación.</small>
        `;
        return header;
    }

    #entrySection(experience, mode) {
        const section = fieldset("Entrada");

        section.append(
            selectField({
                label: "Tipo",
                name: "intro.mode",
                value: mode,
                options: EXPERIENCE_INTRO_MODES.map((value) => [
                    value,
                    MODE_LABELS[value] || value,
                ]),
                onChange: () => this.#commitFromForm(),
            }),
        );

        if (mode !== "NONE") {
            section.append(
                textField({
                    label: "Texto de apertura",
                    name: "intro.openLabel",
                    value: experience.intro.openLabel,
                    onInput: () => this.#commitFromForm(),
                }),
            );
        }

        if (mode === "ENVELOPE") {
            section.append(
                textField({
                    label: "Monograma",
                    name: "intro.envelope.monogram",
                    value: experience.intro.envelope.monogram,
                    onInput: () => this.#commitFromForm(),
                }),
                textAreaField({
                    label: "Mensaje",
                    name: "intro.envelope.message",
                    value: experience.intro.envelope.message,
                    onInput: () => this.#commitFromForm(),
                }),
                selectField({
                    label: "Fondo",
                    name: "intro.envelope.backgroundAssetId",
                    value: experience.intro.envelope.backgroundAssetId || "",
                    options: this.#assetOptions("IMAGE", true),
                    onChange: () => this.#commitFromForm(),
                }),
                selectField({
                    label: "Sello",
                    name: "intro.envelope.sealAssetId",
                    value: experience.intro.envelope.sealAssetId || "",
                    options: this.#assetOptions("IMAGE", true),
                    onChange: () => this.#commitFromForm(),
                }),
            );
        }

        if (mode === "IMAGE" || mode === "GIF") {
            section.append(
                selectField({
                    label: "Asset",
                    name: "intro.assetId",
                    value: experience.intro.assetId || "",
                    options: this.#assetOptions("IMAGE", true, {
                        animatedOnly: mode === "GIF",
                    }),
                    onChange: () => this.#commitFromForm(),
                }),
                this.#mediaComposer(experience, mode),
            );
        }

        if (mode === "VIDEO") {
            section.append(
                selectField({
                    label: "Video",
                    name: "intro.assetId",
                    value: experience.intro.assetId || "",
                    options: this.#assetOptions("VIDEO", true),
                    onChange: () => this.#commitFromForm(),
                }),
                selectField({
                    label: "Poster",
                    name: "intro.posterAssetId",
                    value: experience.intro.posterAssetId || "",
                    options: this.#assetOptions("IMAGE", true),
                    onChange: () => this.#commitFromForm(),
                }),
                checkboxField({
                    label: "Controles",
                    name: "intro.video.controls",
                    checked: experience.intro.video.controls,
                    onChange: () => this.#commitFromForm(),
                }),
                checkboxField({
                    label: "Silenciado",
                    name: "intro.video.muted",
                    checked: experience.intro.video.muted,
                    onChange: () => this.#commitFromForm(),
                }),
                checkboxField({
                    label: "Permitir saltar",
                    name: "intro.allowSkip",
                    checked: experience.intro.allowSkip,
                    onChange: () => this.#commitFromForm(),
                }),
                this.#mediaComposer(experience, mode),
            );
        }

        return section;
    }

    #mediaComposer(experience, mode) {
        const composer = document.createElement("div");
        composer.className = "experience-media-composer";
        composer.dataset.r3ExperienceMediaComposer = "1";

        const heading = document.createElement("div");
        heading.className = "experience-media-composer__heading";
        heading.innerHTML = `
            <strong>Encuadre móvil</strong>
            <small>Ajusta cómo se verá este recurso en la pantalla.</small>
        `;

        const device = EXPERIENCE_PREVIEW_DEVICES[
            this.previewDeviceKey
        ] || EXPERIENCE_PREVIEW_DEVICES.iphone_13;

        const preview = document.createElement("div");
        preview.className = "experience-media-composer__preview";
        preview.style.setProperty(
            "--experience-preview-ratio",
            `${device.width} / ${device.height}`,
        );
        preview.style.backgroundColor =
            experience.intro.backgroundColor || "#000000";
        preview.dataset.r3ExperienceMediaPreview = "1";

        const asset = this.assets?.get?.(
            experience.intro.assetId,
        ) || null;
        const poster = this.assets?.get?.(
            experience.intro.posterAssetId,
        ) || null;

        const media = this.#previewMedia(
            mode,
            asset,
            poster,
            experience.intro,
        );

        if (media) {
            preview.append(media);
        } else {
            const empty = document.createElement("div");
            empty.className =
                "experience-media-composer__empty";
            empty.textContent =
                "Selecciona un recurso para previsualizarlo.";
            preview.append(empty);
        }

        const deviceField = selectField({
            label: "Dispositivo",
            name: "experience.previewDevice",
            value: this.previewDeviceKey,
            options: Object.entries(
                EXPERIENCE_PREVIEW_DEVICES,
            ).map(([key, value]) => [
                key,
                `${value.label} · ${value.width}×${value.height}`,
            ]),
            onChange: (event) => {
                this.previewDeviceKey =
                    event.target.value;
                this.#updateComposerDevicePreview();
            },
        });

        const fitField = selectField({
            label: "Ajuste",
            name: "intro.fit",
            value: experience.intro.fit,
            options: [
                ["cover", "Cover · llenar pantalla"],
                ["contain", "Contain · mostrar completo"],
            ],
            onChange: () => {
                this.#updateComposerPreviewFromForm();
                this.#commitFromForm({
                    suppressRender: true,
                });
            },
        });

        const position = experience.intro.mediaPosition;
        const xField = positionRangeField({
            label: "Posición X",
            name: "intro.mediaPosition.x",
            value: position.x,
            min: 0,
            max: 100,
            step: 1,
            suffix: "%",
            onInput: () =>
                this.#updateComposerPreviewFromForm(),
            onChange: () =>
                this.#commitFromForm({
                    suppressRender: true,
                }),
        });
        const yField = positionRangeField({
            label: "Posición Y",
            name: "intro.mediaPosition.y",
            value: position.y,
            min: 0,
            max: 100,
            step: 1,
            suffix: "%",
            onInput: () =>
                this.#updateComposerPreviewFromForm(),
            onChange: () =>
                this.#commitFromForm({
                    suppressRender: true,
                }),
        });
        const scaleField = positionRangeField({
            label: "Escala",
            name: "intro.mediaScale",
            value: experience.intro.mediaScale,
            min: 0.5,
            max: 2,
            step: 0.05,
            suffix: "×",
            onInput: () =>
                this.#updateComposerPreviewFromForm(),
            onChange: () =>
                this.#commitFromForm({
                    suppressRender: true,
                }),
        });

        const background = colorField({
            label: "Fondo",
            name: "intro.backgroundColor",
            value: experience.intro.backgroundColor,
            onInput: () =>
                this.#updateComposerPreviewFromForm(),
            onChange: () =>
                this.#commitFromForm({
                    suppressRender: true,
                }),
        });

        composer.append(
            heading,
            preview,
            deviceField,
            fitField,
            this.#positionPresets(position),
            xField,
            yField,
            scaleField,
            background,
        );

        return composer;
    }

    #previewMedia(mode, asset, poster, intro) {
        if (!asset?.url) {
            return null;
        }

        const media = document.createElement(
            mode === "VIDEO"
                ? "video"
                : "img",
        );
        media.className =
            "experience-media-composer__media";
        media.dataset.r3ExperienceMediaPreviewAsset = "1";

        if (mode === "VIDEO") {
            media.src = asset.url;
            media.poster = poster?.url || "";
            media.muted = true;
            media.playsInline = true;
            media.preload = "metadata";
        } else {
            media.src = asset.url;
            media.alt = "";
        }

        applyPreviewPlacement(media, intro);
        return media;
    }

    #positionPresets(position) {
        const wrapper = document.createElement("div");
        wrapper.className =
            "experience-media-composer__presets";

        const label = document.createElement("span");
        label.textContent = "Punto focal";

        const grid = document.createElement("div");
        grid.className =
            "experience-media-composer__preset-grid";

        for (const preset of MEDIA_POSITION_PRESETS) {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = preset.symbol;
            button.title = preset.label;
            button.dataset.r3MediaPreset =
                `${preset.x}-${preset.y}`;

            if (
                Number(position.x) === preset.x
                && Number(position.y) === preset.y
            ) {
                button.classList.add("is-active");
            }

            button.addEventListener("click", () => {
                this.#setComposerPosition(
                    preset.x,
                    preset.y,
                );
                this.#updateComposerPreviewFromForm();
                this.#commitFromForm({
                    suppressRender: true,
                    statusMessage:
                        `Punto focal: ${preset.label}.`,
                });
                this.#syncPresetActiveState(
                    preset.x,
                    preset.y,
                );
            });
            grid.append(button);
        }

        wrapper.append(label, grid);
        return wrapper;
    }

    #updateComposerDevicePreview() {
        const preview = this.root.querySelector(
            "[data-r3-experience-media-preview='1']"
        );
        if (!preview) {
            return;
        }

        const device = EXPERIENCE_PREVIEW_DEVICES[
            this.previewDeviceKey
        ] || EXPERIENCE_PREVIEW_DEVICES.iphone_13;

        preview.style.setProperty(
            "--experience-preview-ratio",
            `${device.width} / ${device.height}`,
        );
    }

    #updateComposerPreviewFromForm() {
        const preview = this.root.querySelector(
            "[data-r3-experience-media-preview='1']"
        );
        const media = this.root.querySelector(
            "[data-r3-experience-media-preview-asset='1']"
        );

        if (!preview) {
            return;
        }

        const current = normalizeExperience(
            this.state.document.experience,
        );

        current.intro.fit =
            valueOf(this.root, "intro.fit")
            || current.intro.fit;
        current.intro.mediaPosition = {
            x: numberValueOf(
                this.root,
                "intro.mediaPosition.x",
                current.intro.mediaPosition.x,
            ),
            y: numberValueOf(
                this.root,
                "intro.mediaPosition.y",
                current.intro.mediaPosition.y,
            ),
        };
        current.intro.mediaScale =
            numberValueOf(
                this.root,
                "intro.mediaScale",
                current.intro.mediaScale,
            );
        current.intro.backgroundColor =
            valueOf(
                this.root,
                "intro.backgroundColor",
            )
            || current.intro.backgroundColor;

        preview.style.backgroundColor =
            current.intro.backgroundColor;

        if (media) {
            applyPreviewPlacement(
                media,
                current.intro,
            );
        }

        this.#syncPresetActiveState(
            current.intro.mediaPosition.x,
            current.intro.mediaPosition.y,
        );
    }

    #setComposerPosition(x, y) {
        const xInput = this.root.querySelector(
            `[name="${cssEscape("intro.mediaPosition.x")}"]`,
        );
        const yInput = this.root.querySelector(
            `[name="${cssEscape("intro.mediaPosition.y")}"]`,
        );

        if (xInput) {
            xInput.value = String(x);
            syncRangeOutput(xInput, "%");
        }
        if (yInput) {
            yInput.value = String(y);
            syncRangeOutput(yInput, "%");
        }
    }

    #syncPresetActiveState(x, y) {
        for (
            const button
            of this.root.querySelectorAll(
                "[data-r3-media-preset]"
            )
        ) {
            const [presetX, presetY] =
                String(
                    button.dataset.r3MediaPreset
                    || ""
                )
                    .split("-")
                    .map(Number);

            button.classList.toggle(
                "is-active",
                presetX === Number(x)
                && presetY === Number(y),
            );
        }
    }

    #musicSection(experience) {
        const section = fieldset("Música");

        section.append(
            checkboxField({
                label: "Activada",
                name: "audio.enabled",
                checked: experience.audio.enabled,
                onChange: () => this.#commitFromForm(),
            }),
            selectField({
                label: "Audio",
                name: "audio.assetId",
                value: experience.audio.assetId || "",
                options: this.#assetOptions("AUDIO", true),
                onChange: () => this.#commitFromForm(),
            }),
            rangeField({
                label: "Volumen",
                name: "audio.volume",
                value: experience.audio.volume,
                onInput: () => this.#commitFromForm(),
            }),
            checkboxField({
                label: "Loop",
                name: "audio.loop",
                checked: experience.audio.loop,
                onChange: () => this.#commitFromForm(),
            }),
            checkboxField({
                label: "Control visible",
                name: "audio.showControl",
                checked: experience.audio.showControl,
                onChange: () => this.#commitFromForm(),
            }),
            selectField({
                label: "Inicio",
                name: "audio.startPolicy",
                value: experience.audio.startPolicy,
                options: EXPERIENCE_AUDIO_START_POLICIES.map((value) => [
                    value,
                    POLICY_LABELS[value] || value,
                ]),
                onChange: () => this.#commitFromForm(),
            }),
        );

        return section;
    }

    #actions() {
        const actions = document.createElement("div");
        actions.className = "experience-panel__actions";

        const preview = document.createElement("button");
        preview.type = "button";
        preview.textContent = "Probar experiencia";
        preview.dataset.r3ExperiencePreview = "1";
        preview.addEventListener("click", () => {
            this.onPreview?.();
            this.onStatus?.("Experiencia lista para probar.");
        });

        const reset = document.createElement("button");
        reset.type = "button";
        reset.textContent = "Reiniciar experiencia";
        reset.dataset.r3ExperienceReset = "1";
        reset.addEventListener("click", () => {
            this.onResetPreview?.();
            this.onStatus?.("Experiencia reiniciada.");
        });

        actions.append(preview, reset);
        return actions;
    }

    #commitFromForm(options = {}) {
        const {
            suppressRender = false,
            statusMessage =
                "Experiencia actualizada.",
        } = options;

        const current = normalizeExperience(
            this.state.document.experience,
        );
        const mode = valueOf(this.root, "intro.mode") || "NONE";

        current.intro.mode = mode;
        current.intro.enabled = mode !== "NONE";
        current.intro.openLabel =
            valueOf(this.root, "intro.openLabel")
            || current.intro.openLabel;
        current.intro.assetId =
            nullable(valueOf(this.root, "intro.assetId"));
        current.intro.posterAssetId =
            nullable(valueOf(this.root, "intro.posterAssetId"));
        current.intro.fit =
            valueOf(this.root, "intro.fit")
            || current.intro.fit;
        current.intro.mediaPosition = {
            x: numberValueOf(
                this.root,
                "intro.mediaPosition.x",
                current.intro.mediaPosition.x,
            ),
            y: numberValueOf(
                this.root,
                "intro.mediaPosition.y",
                current.intro.mediaPosition.y,
            ),
        };
        current.intro.mediaScale =
            numberValueOf(
                this.root,
                "intro.mediaScale",
                current.intro.mediaScale,
            );
        current.intro.backgroundColor =
            valueOf(this.root, "intro.backgroundColor")
            || current.intro.backgroundColor;
        current.intro.allowSkip =
            checkedOf(this.root, "intro.allowSkip", current.intro.allowSkip);
        current.intro.envelope.backgroundAssetId =
            nullable(valueOf(this.root, "intro.envelope.backgroundAssetId"));
        current.intro.envelope.sealAssetId =
            nullable(valueOf(this.root, "intro.envelope.sealAssetId"));
        current.intro.envelope.monogram =
            valueOf(this.root, "intro.envelope.monogram")
            ?? current.intro.envelope.monogram;
        current.intro.envelope.message =
            valueOf(this.root, "intro.envelope.message")
            ?? current.intro.envelope.message;
        current.intro.video.controls =
            checkedOf(this.root, "intro.video.controls", current.intro.video.controls);
        current.intro.video.muted =
            checkedOf(this.root, "intro.video.muted", current.intro.video.muted);

        current.audio.enabled =
            checkedOf(this.root, "audio.enabled", current.audio.enabled);
        current.audio.assetId =
            nullable(valueOf(this.root, "audio.assetId"));
        current.audio.volume =
            Number(valueOf(this.root, "audio.volume") ?? current.audio.volume);
        current.audio.loop =
            checkedOf(this.root, "audio.loop", current.audio.loop);
        current.audio.showControl =
            checkedOf(this.root, "audio.showControl", current.audio.showControl);
        current.audio.startPolicy =
            valueOf(this.root, "audio.startPolicy")
            || current.audio.startPolicy;

        if (suppressRender) {
            this.suppressNextExperienceRender = true;
        }

        this.state.updateExperience(current);
        this.onStatus?.(statusMessage);
    }

    #assetOptions(type, includeEmpty = false, options = {}) {
        const list = this.assets?.list?.({ type }) || [];
        const filtered = options.animatedOnly
            ? list.filter((asset) => asset.metadata?.animated)
            : list;
        const values = filtered.map((asset) => [
            asset.id,
            asset.name,
        ]);

        return includeEmpty
            ? [["", "Sin seleccionar"], ...values]
            : values;
    }
}

function applyPreviewPlacement(media, intro = {}) {
    const position = intro.mediaPosition || {
        x: 50,
        y: 50,
    };
    const x = Number(position.x ?? 50);
    const y = Number(position.y ?? 50);
    const scale = Number(intro.mediaScale ?? 1);

    media.style.objectFit = intro.fit || "cover";
    media.style.objectPosition = `${x}% ${y}%`;
    media.style.transform = `scale(${scale})`;
    media.style.transformOrigin = `${x}% ${y}%`;
}

function positionRangeField({
    label,
    name,
    value,
    min,
    max,
    step,
    suffix = "",
    onInput,
    onChange,
}) {
    const field = baseField(label);
    field.classList.add(
        "experience-panel__field--range",
    );

    const row = document.createElement("div");
    row.className =
        "experience-panel__range-row";

    const input = document.createElement("input");
    input.name = name;
    input.type = "range";
    input.min = String(min);
    input.max = String(max);
    input.step = String(step);
    input.value = String(value);

    const output = document.createElement("output");
    output.textContent = `${value}${suffix}`;

    input.addEventListener("input", (event) => {
        output.textContent =
            `${event.target.value}${suffix}`;
        onInput?.(event);
    });
    input.addEventListener("change", (event) => {
        onChange?.(event);
    });

    row.append(input, output);
    field.append(row);
    return field;
}

function syncRangeOutput(input, suffix = "") {
    const row = input?.closest?.(
        ".experience-panel__range-row",
    );
    const output = row?.querySelector?.("output");
    if (output) {
        output.textContent =
            `${input.value}${suffix}`;
    }
}

function fieldset(title) {
    const section = document.createElement("section");
    section.className = "experience-panel__section";
    const heading = document.createElement("h3");
    heading.textContent = title;
    section.append(heading);
    return section;
}

function selectField({ label, name, value, options, onChange }) {
    const field = baseField(label);
    const select = document.createElement("select");
    select.name = name;
    for (const [optionValue, optionLabel] of options) {
        const option = document.createElement("option");
        option.value = optionValue;
        option.textContent = optionLabel;
        option.selected = String(optionValue) === String(value || "");
        select.append(option);
    }
    select.addEventListener("change", onChange);
    field.append(select);
    return field;
}

function textField({ label, name, value, onInput }) {
    const field = baseField(label);
    const input = document.createElement("input");
    input.name = name;
    input.type = "text";
    input.value = value || "";
    input.addEventListener("input", onInput);
    field.append(input);
    return field;
}

function textAreaField({ label, name, value, onInput }) {
    const field = baseField(label);
    const textarea = document.createElement("textarea");
    textarea.name = name;
    textarea.rows = 3;
    textarea.value = value || "";
    textarea.addEventListener("input", onInput);
    field.append(textarea);
    return field;
}

function colorField({
    label,
    name,
    value,
    onInput,
    onChange,
}) {
    const field = baseField(label);
    const input = document.createElement("input");
    input.name = name;
    input.type = "color";
    input.value = value || "#000000";
    input.addEventListener("input", onInput);
    input.addEventListener("change", onChange);
    field.append(input);
    return field;
}

function rangeField({ label, name, value, onInput }) {
    const field = baseField(label);
    const input = document.createElement("input");
    input.name = name;
    input.type = "range";
    input.min = "0";
    input.max = "1";
    input.step = "0.05";
    input.value = String(value ?? 0.7);
    input.addEventListener("input", onInput);
    field.append(input);
    return field;
}

function checkboxField({ label, name, checked, onChange }) {
    const field = document.createElement("label");
    field.className = "experience-panel__check";
    const input = document.createElement("input");
    input.name = name;
    input.type = "checkbox";
    input.checked = Boolean(checked);
    input.addEventListener("change", onChange);
    const text = document.createElement("span");
    text.textContent = label;
    field.append(input, text);
    return field;
}

function baseField(labelText) {
    const label = document.createElement("label");
    label.className = "experience-panel__field";
    const span = document.createElement("span");
    span.textContent = labelText;
    label.append(span);
    return label;
}

function valueOf(root, name) {
    return root.querySelector(`[name="${cssEscape(name)}"]`)?.value;
}

function numberValueOf(root, name, fallback) {
    const raw = valueOf(root, name);
    if (raw === undefined || raw === null || raw === "") {
        return fallback;
    }

    const number = Number(raw);
    return Number.isFinite(number)
        ? number
        : fallback;
}

function checkedOf(root, name, fallback) {
    const input = root.querySelector(`[name="${cssEscape(name)}"]`);
    return input ? Boolean(input.checked) : fallback;
}

function nullable(value) {
    return value ? String(value) : null;
}

function cssEscape(value) {
    if (globalThis.CSS?.escape) {
        return globalThis.CSS.escape(String(value));
    }

    return String(value).replace(/["\\]/g, "\\$&");
}
