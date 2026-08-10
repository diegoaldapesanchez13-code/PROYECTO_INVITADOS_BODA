import assert from "node:assert/strict";
import test from "node:test";

import {
    createDefaultExperience,
    EXPERIENCE_AUDIO_START_POLICIES,
    EXPERIENCE_INTRO_MODES,
    normalizeExperience,
    validateExperience,
} from "../experience/contract.js";
import {
    normalizeDocumentV4,
    validateDocumentV4,
} from "../core/schema_v4.js";

function baseDocument(overrides = {}) {
    return {
        schemaVersion: 4,
        page: {
            id: "page",
            name: "Boda",
            type: "PAGE",
            settings: {},
        },
        canvases: [
            {
                id: "canvas-1",
                type: "CANVAS",
                name: "Lienzo 1",
                parentId: null,
                canvasId: "canvas-1",
                children: ["image-1"],
            },
        ],
        nodes: [
            {
                id: "image-1",
                type: "IMAGE",
                parentId: "canvas-1",
                canvasId: "canvas-1",
                children: [],
            },
        ],
        assets: [
            {
                id: "asset-1",
                type: "IMAGE",
                url: "/media/foto.jpg",
            },
        ],
        responsive: {
            baseDevice: "mobile",
            inheritance: {
                tablet: "mobile",
                desktop: "tablet",
            },
        },
        meta: {},
        ...overrides,
    };
}

test("H.1 V4 document without experience receives safe defaults", () => {
    const document = normalizeDocumentV4(baseDocument());

    assert.equal(document.schemaVersion, 4);
    assert.equal(document.experience.intro.enabled, false);
    assert.equal(document.experience.intro.mode, "NONE");
    assert.equal(document.experience.audio.enabled, false);
    assert.equal(document.experience.audio.volume, 0.7);

    assert.equal(validateDocumentV4(document).valid, true);
});

test("H.1 default experience contract is stable", () => {
    const defaults = createDefaultExperience();

    assert.deepEqual(defaults, {
        intro: {
            enabled: false,
            mode: "NONE",
            assetId: null,
            posterAssetId: null,
            backgroundColor: "#000000",
            fit: "cover",
            mediaPosition: { x: 50, y: 50 },
            mediaScale: 1,
            clickAnywhere: true,
            showOpenLabel: true,
            openLabel: "Abrir invitación",
            allowSkip: true,
            transition: {
                type: "FADE",
                durationMs: 500,
            },
            envelope: {
                palette: "CLASSIC",
                backgroundAssetId: null,
                sealAssetId: null,
                monogram: "",
                message: "",
                animation: "CLASSIC",
            },
            video: {
                controls: false,
                muted: false,
                playsInline: true,
                transitionOnEnded: true,
            },
        },
        audio: {
            enabled: false,
            assetId: null,
            volume: 0.7,
            loop: true,
            showControl: true,
            startPolicy: "AFTER_INTRO",
        },
    });
});

test("H.1 all official intro modes normalize and validate", () => {
    for (const mode of EXPERIENCE_INTRO_MODES) {
        const experience = normalizeExperience({
            intro: {
                enabled: mode !== "NONE",
                mode,
                assetId: mode === "NONE" ? null : "asset-intro",
            },
        });

        assert.equal(experience.intro.mode, mode);
        assert.equal(
            experience.intro.enabled,
            mode === "NONE" ? false : true,
        );
        assert.equal(validateExperience(experience).valid, true);
    }
});

test("H.1 audio disabled and enabled policies normalize and validate", () => {
    const disabled = normalizeExperience({
        audio: {
            enabled: false,
        },
    });
    assert.equal(disabled.audio.enabled, false);
    assert.equal(validateExperience(disabled).valid, true);

    for (const startPolicy of EXPERIENCE_AUDIO_START_POLICIES) {
        const enabled = normalizeExperience({
            audio: {
                enabled: true,
                assetId: "audio-1",
                volume: 0.35,
                loop: false,
                showControl: false,
                startPolicy,
            },
        });

        assert.equal(enabled.audio.enabled, true);
        assert.equal(enabled.audio.assetId, "audio-1");
        assert.equal(enabled.audio.volume, 0.35);
        assert.equal(enabled.audio.loop, false);
        assert.equal(enabled.audio.showControl, false);
        assert.equal(enabled.audio.startPolicy, startPolicy);
        assert.equal(validateExperience(enabled).valid, true);
    }
});

test("H.1 invalid values are rejected by validators", () => {
    const invalid = createDefaultExperience({
        intro: {
            mode: "SPINNER",
        },
    });

    invalid.intro.mode = "SPINNER";
    invalid.intro.fit = "stretch";
    invalid.intro.backgroundColor = "black";
    invalid.intro.transition.type = "SLIDE";
    invalid.intro.transition.durationMs = -1;
    invalid.audio.volume = 2;
    invalid.audio.startPolicy = "AUTO";

    const experienceValidation = validateExperience(invalid);
    assert.equal(experienceValidation.valid, false);
    assert.match(experienceValidation.errors.join("\n"), /mode/);
    assert.match(experienceValidation.errors.join("\n"), /startPolicy/);

    const documentValidation = validateDocumentV4(
        baseDocument({ experience: invalid }),
    );
    assert.equal(documentValidation.valid, false);
    assert.match(documentValidation.errors.join("\n"), /experience/);
});

test("H.1 normalize is idempotent and keeps hierarchy outside experience", () => {
    const source = baseDocument({
        experience: {
            intro: {
                enabled: true,
                mode: "ENVELOPE",
                openLabel: "Entrar",
                envelope: {
                    monogram: "F&D",
                    message: "Nos casamos",
                },
            },
            audio: {
                enabled: true,
                assetId: "song-1",
                volume: 0.9,
                startPolicy: "ON_OPEN_GESTURE",
            },
        },
    });

    const first = normalizeDocumentV4(source);
    const second = normalizeDocumentV4(first);

    assert.deepEqual(second, first);
    assert.equal(first.canvases.length, 1);
    assert.equal(first.nodes.length, 1);
    assert.equal(first.canvases[0].children[0], "image-1");
    assert.equal(first.nodes[0].parentId, "canvas-1");
    assert.equal(first.nodes[0].canvasId, "canvas-1");
});
