export const EXPERIENCE_INTRO_MODES = Object.freeze([
    "NONE",
    "ENVELOPE",
    "IMAGE",
    "GIF",
    "VIDEO",
]);

export const EXPERIENCE_AUDIO_START_POLICIES = Object.freeze([
    "MANUAL",
    "ON_OPEN_GESTURE",
    "AFTER_INTRO",
]);

const INTRO_FITS = Object.freeze(["cover", "contain"]);
const TRANSITION_TYPES = Object.freeze(["FADE"]);
const ENVELOPE_PALETTES = Object.freeze([
    "CLASSIC",
    "BOSQUE",
    "ROSA",
    "TERRACOTA",
    "AZUL",
    "LAVANDA",
    "DORADO",
    "TINTA_MARFIL",
    "NEGRO_DORADO",
    "VINO_ROSA",
    "SALVIA_PERLA",
    "PERSONALIZADA",
]);
const ENVELOPE_ANIMATIONS = Object.freeze(["CLASSIC"]);

export function createDefaultExperience(overrides = {}) {
    return normalizeExperience(overrides);
}

export function normalizeExperience(input = {}) {
    const source = isRecord(input) ? input : {};
    const introSource = isRecord(source.intro) ? source.intro : {};
    const audioSource = isRecord(source.audio) ? source.audio : {};

    const mode = normalizeEnum(
        introSource.mode,
        EXPERIENCE_INTRO_MODES,
        "NONE",
    );

    return {
        intro: {
            enabled: mode === "NONE" ? false : Boolean(introSource.enabled),
            mode,
            assetId: nullableId(introSource.assetId),
            posterAssetId: nullableId(introSource.posterAssetId),
            backgroundColor: normalizeColor(
                introSource.backgroundColor,
                "#000000",
            ),
            fit: normalizeEnum(introSource.fit, INTRO_FITS, "cover"),
            mediaPosition: normalizeMediaPosition(
                introSource.mediaPosition,
            ),
            mediaScale: normalizeDecimal(
                introSource.mediaScale,
                1,
                {
                    min: 0.5,
                    max: 2,
                },
            ),
            clickAnywhere: introSource.clickAnywhere !== false,
            showOpenLabel: introSource.showOpenLabel !== false,
            openLabel: normalizeText(
                introSource.openLabel,
                "Abrir invitación",
            ),
            allowSkip: introSource.allowSkip !== false,
            transition: normalizeTransition(introSource.transition),
            envelope: normalizeEnvelope(introSource.envelope),
            video: normalizeVideoIntro(introSource.video),
        },
        audio: {
            enabled: Boolean(audioSource.enabled),
            assetId: nullableId(audioSource.assetId),
            volume: normalizeVolume(audioSource.volume, 0.7),
            loop: audioSource.loop !== false,
            showControl: audioSource.showControl !== false,
            startPolicy: normalizeEnum(
                audioSource.startPolicy,
                EXPERIENCE_AUDIO_START_POLICIES,
                "AFTER_INTRO",
            ),
        },
    };
}

export function validateExperience(input) {
    const errors = [];

    if (!isRecord(input)) {
        return {
            valid: false,
            errors: ["experience debe ser un objeto."],
        };
    }

    const intro = input.intro;
    const audio = input.audio;

    if (!isRecord(intro)) {
        errors.push("experience.intro debe ser un objeto.");
    } else {
        if (!EXPERIENCE_INTRO_MODES.includes(intro.mode)) {
            errors.push(
                `experience.intro.mode inválido: ${String(intro.mode)}.`
            );
        }

        if (!INTRO_FITS.includes(intro.fit)) {
            errors.push(
                `experience.intro.fit inválido: ${String(intro.fit)}.`
            );
        }

        validateMediaPosition(intro.mediaPosition, errors);

        if (
            typeof intro.mediaScale !== "number"
            || !Number.isFinite(intro.mediaScale)
            || intro.mediaScale < 0.5
            || intro.mediaScale > 2
        ) {
            errors.push(
                "experience.intro.mediaScale debe estar entre 0.5 y 2."
            );
        }

        validateOptionalId(
            intro.assetId,
            "experience.intro.assetId",
            errors,
        );
        validateOptionalId(
            intro.posterAssetId,
            "experience.intro.posterAssetId",
            errors,
        );

        if (!isHexColor(intro.backgroundColor)) {
            errors.push(
                "experience.intro.backgroundColor debe ser color hex."
            );
        }

        validateTransition(intro.transition, errors);
        validateEnvelope(intro.envelope, errors);
        validateVideoIntro(intro.video, errors);
    }

    if (!isRecord(audio)) {
        errors.push("experience.audio debe ser un objeto.");
    } else {
        validateOptionalId(
            audio.assetId,
            "experience.audio.assetId",
            errors,
        );

        if (
            typeof audio.volume !== "number"
            || !Number.isFinite(audio.volume)
            || audio.volume < 0
            || audio.volume > 1
        ) {
            errors.push("experience.audio.volume debe estar entre 0 y 1.");
        }

        if (!EXPERIENCE_AUDIO_START_POLICIES.includes(audio.startPolicy)) {
            errors.push(
                `experience.audio.startPolicy inválido: ${String(audio.startPolicy)}.`
            );
        }
    }

    return {
        valid: errors.length === 0,
        errors,
    };
}

function normalizeMediaPosition(input = {}) {
    const source = isRecord(input) ? input : {};

    return {
        x: normalizeDecimal(source.x, 50, {
            min: 0,
            max: 100,
        }),
        y: normalizeDecimal(source.y, 50, {
            min: 0,
            max: 100,
        }),
    };
}

function validateMediaPosition(position, errors) {
    if (!isRecord(position)) {
        errors.push(
            "experience.intro.mediaPosition debe ser un objeto."
        );
        return;
    }

    for (const axis of ["x", "y"]) {
        const value = position[axis];
        if (
            typeof value !== "number"
            || !Number.isFinite(value)
            || value < 0
            || value > 100
        ) {
            errors.push(
                `experience.intro.mediaPosition.${axis} debe estar entre 0 y 100.`
            );
        }
    }
}

function normalizeTransition(input = {}) {
    const source = isRecord(input) ? input : {};

    return {
        type: normalizeEnum(source.type, TRANSITION_TYPES, "FADE"),
        durationMs: normalizeInteger(source.durationMs, 500, {
            min: 0,
            max: 10000,
        }),
    };
}

function normalizeEnvelope(input = {}) {
    const source = isRecord(input) ? input : {};

    return {
        palette: normalizeEnum(
            source.palette,
            ENVELOPE_PALETTES,
            "CLASSIC",
        ),
        backgroundAssetId: nullableId(source.backgroundAssetId),
        sealAssetId: nullableId(source.sealAssetId),
        monogram: normalizeText(source.monogram, ""),
        message: normalizeText(source.message, ""),
        animation: normalizeEnum(
            source.animation,
            ENVELOPE_ANIMATIONS,
            "CLASSIC",
        ),
    };
}

function normalizeVideoIntro(input = {}) {
    const source = isRecord(input) ? input : {};

    return {
        controls: Boolean(source.controls),
        muted: Boolean(source.muted),
        playsInline: source.playsInline !== false,
        transitionOnEnded: source.transitionOnEnded !== false,
    };
}

function validateTransition(transition, errors) {
    if (!isRecord(transition)) {
        errors.push("experience.intro.transition debe ser un objeto.");
        return;
    }

    if (!TRANSITION_TYPES.includes(transition.type)) {
        errors.push(
            `experience.intro.transition.type inválido: ${String(transition.type)}.`
        );
    }

    if (
        !Number.isInteger(transition.durationMs)
        || transition.durationMs < 0
    ) {
        errors.push(
            "experience.intro.transition.durationMs debe ser entero positivo."
        );
    }
}

function validateEnvelope(envelope, errors) {
    if (!isRecord(envelope)) {
        errors.push("experience.intro.envelope debe ser un objeto.");
        return;
    }

    if (!ENVELOPE_PALETTES.includes(envelope.palette)) {
        errors.push(
            `experience.intro.envelope.palette inválido: ${String(envelope.palette)}.`
        );
    }

    if (!ENVELOPE_ANIMATIONS.includes(envelope.animation)) {
        errors.push(
            `experience.intro.envelope.animation inválido: ${String(envelope.animation)}.`
        );
    }

    validateOptionalId(
        envelope.backgroundAssetId,
        "experience.intro.envelope.backgroundAssetId",
        errors,
    );
    validateOptionalId(
        envelope.sealAssetId,
        "experience.intro.envelope.sealAssetId",
        errors,
    );
}

function validateVideoIntro(video, errors) {
    if (!isRecord(video)) {
        errors.push("experience.intro.video debe ser un objeto.");
    }
}

function normalizeEnum(value, allowed, fallback) {
    const normalized =
        typeof value === "string"
            ? value.trim()
            : "";

    return allowed.includes(normalized)
        ? normalized
        : fallback;
}

function normalizeText(value, fallback) {
    return typeof value === "string"
        ? value
        : fallback;
}

function nullableId(value) {
    if (value === null || value === undefined || value === "") {
        return null;
    }

    return String(value);
}

function validateOptionalId(value, field, errors) {
    if (
        value !== null
        && value !== undefined
        && typeof value !== "string"
    ) {
        errors.push(`${field} debe ser string o null.`);
    }
}

function normalizeColor(value, fallback) {
    return isHexColor(value) ? value : fallback;
}

function isHexColor(value) {
    return (
        typeof value === "string"
        && /^#[0-9a-fA-F]{6}$/.test(value)
    );
}

function normalizeVolume(value, fallback) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return fallback;
    }
    return Math.min(1, Math.max(0, number));
}

function normalizeDecimal(value, fallback, options = {}) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return fallback;
    }

    const min = Number.isFinite(options.min)
        ? options.min
        : number;
    const max = Number.isFinite(options.max)
        ? options.max
        : number;

    return Math.min(max, Math.max(min, number));
}

function normalizeInteger(value, fallback, options = {}) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
        return fallback;
    }

    const integer = Math.trunc(number);
    const min = Number.isFinite(options.min)
        ? options.min
        : integer;
    const max = Number.isFinite(options.max)
        ? options.max
        : integer;

    return Math.min(max, Math.max(min, integer));
}

function isRecord(value) {
    return (
        value !== null
        && typeof value === "object"
        && !Array.isArray(value)
    );
}
