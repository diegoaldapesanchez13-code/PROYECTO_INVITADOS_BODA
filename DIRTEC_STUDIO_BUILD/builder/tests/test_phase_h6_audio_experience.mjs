import assert from "node:assert/strict";
import test from "node:test";

import { AssetManager, ASSET_TYPES, normalizeAsset } from "../assets/asset_manager.js";
import { AssetUploadService, categoryFromType, typeFromMime } from "../assets/uploads.js";
import { AudioController } from "../experience/audio_controller.js";
import {
    ExperienceController,
    EXPERIENCE_STATES,
} from "../experience/controller.js";

class FakeElement {
    constructor(tagName = "div", ownerDocument = null) {
        this.tagName = String(tagName).toUpperCase();
        this.ownerDocument = ownerDocument;
        this.children = [];
        this.dataset = {};
        this.attributes = new Map();
        this.listeners = new Map();
        this.hidden = false;
        this.textContent = "";
        this.className = "";
        this.style = {};
        this.parentNode = null;
        this.onerror = null;
        this.onended = null;
    }

    append(...children) {
        for (const child of children) {
            child.parentNode = this;
            this.children.push(child);
        }
    }

    remove() {
        if (!this.parentNode) {
            return;
        }
        this.parentNode.children = this.parentNode.children.filter(
            (child) => child !== this,
        );
        this.parentNode = null;
    }

    setAttribute(name, value) {
        this.attributes.set(name, String(value));
    }

    addEventListener(name, listener) {
        this.listeners.set(name, listener);
    }

    click() {
        this.listeners.get("click")?.({
            type: "click",
            stopPropagation() {},
        });
    }
}

class FakeAudioElement extends FakeElement {
    constructor(ownerDocument, options = {}) {
        super("audio", ownerDocument);
        this.playCalls = 0;
        this.pauseCalls = 0;
        this.rejectPlay = Boolean(options.rejectAudioPlay);
    }

    play() {
        this.playCalls += 1;
        return this.rejectPlay
            ? Promise.reject(new Error("audio blocked"))
            : Promise.resolve();
    }

    pause() {
        this.pauseCalls += 1;
    }
}

class FakeVideoElement extends FakeElement {
    constructor(ownerDocument) {
        super("video", ownerDocument);
        this.playCalls = 0;
    }

    play() {
        this.playCalls += 1;
        return Promise.resolve();
    }

    pause() {}
}

class FakeDocument {
    constructor(options = {}) {
        this.options = options;
        this.createdAudios = [];
        this.createdVideos = [];
    }

    createElement(tagName) {
        const normalized = String(tagName).toLowerCase();
        if (normalized === "audio") {
            const audio = new FakeAudioElement(this, this.options);
            this.createdAudios.push(audio);
            return audio;
        }
        if (normalized === "video") {
            const video = new FakeVideoElement(this);
            this.createdVideos.push(video);
            return video;
        }
        return new FakeElement(tagName, this);
    }
}

function collect(node, result = []) {
    for (const child of node.children || []) {
        result.push(child);
        collect(child, result);
    }
    return result;
}

function byClass(root, className) {
    return collect(root).find((element) =>
        String(element.className || "")
            .split(/\s+/)
            .includes(className)
    );
}

function documentV4(experience) {
    return {
        schemaVersion: 4,
        page: { id: "page", name: "Boda", type: "PAGE", settings: {} },
        canvases: [],
        nodes: [],
        assets: [
            {
                id: "song",
                type: "AUDIO",
                url: "/media/song.mp3",
                metadata: { mediaKind: "AUDIO" },
            },
            {
                id: "intro-video",
                type: "VIDEO",
                url: "/media/intro.mp4",
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
        experience,
    };
}

test("H.6 audio MIME maps to AUDIO asset semantics", () => {
    assert.equal(typeFromMime("audio/mpeg"), ASSET_TYPES.AUDIO);
    assert.equal(typeFromMime("audio/ogg"), ASSET_TYPES.AUDIO);
    assert.equal(categoryFromType(ASSET_TYPES.AUDIO), "Audio");

    const mp3 = normalizeAsset({
        type: ASSET_TYPES.AUDIO,
        url: "/media/song.mp3",
    });
    assert.equal(mp3.mimeType, "audio/mpeg");
    assert.equal(mp3.metadata.mediaKind, "AUDIO");

    const oggVideo = normalizeAsset({
        type: ASSET_TYPES.VIDEO,
        url: "/media/clip.ogg",
    });
    assert.equal(oggVideo.mimeType, "video/ogg");
});

test("H.6 local audio upload uses object URL and no Base64", async () => {
    const originalCreateObjectURL = globalThis.URL?.createObjectURL;
    globalThis.URL.createObjectURL = () => "blob:audio-song";

    try {
        const manager = new AssetManager();
        const service = new AssetUploadService({ manager });
        const file = new File(["audio"], "cancion.mp3", {
            type: "audio/mpeg",
        });

        const asset = await service.importFile(file);

        assert.equal(asset.type, ASSET_TYPES.AUDIO);
        assert.equal(asset.category, "Audio");
        assert.equal(asset.url, "blob:audio-song");
        assert.equal(asset.url.startsWith("data:"), false);
        assert.equal(asset.metadata.mediaKind, "AUDIO");
        assert.equal(asset.metadata.volatileUrl, true);
    } finally {
        globalThis.URL.createObjectURL = originalCreateObjectURL;
    }
});

test("H.6 AudioController handles play pause volume loop and policy", async () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const controller = new AudioController({
        document: fakeDocument,
        root,
        audio: {
            enabled: true,
            assetId: "song",
            volume: 0.35,
            loop: true,
            showControl: true,
            startPolicy: "AFTER_INTRO",
        },
        assetResolver: () => ({ url: "/media/song.mp3" }),
        logger: { warn() {} },
    });

    const started = await controller.start("AFTER_INTRO");
    const audio = fakeDocument.createdAudios[0];

    assert.equal(started, true);
    assert.equal(audio.playCalls, 1);
    assert.equal(audio.volume, 0.35);
    assert.equal(audio.loop, true);
    assert.equal(root.children.length, 1);
    assert.equal(root.children[0].dataset.audioPlaying, "true");

    controller.pause();

    assert.equal(audio.pauseCalls, 1);
    assert.equal(root.children[0].dataset.audioPlaying, "false");
});

test("H.6 manual policy does not autoplay after intro", async () => {
    const fakeDocument = new FakeDocument();
    const controller = new AudioController({
        document: fakeDocument,
        audio: {
            enabled: true,
            assetId: "song",
            startPolicy: "MANUAL",
        },
        assetResolver: () => ({ url: "/media/song.mp3" }),
    });

    assert.equal(await controller.start("AFTER_INTRO"), false);
    assert.equal(fakeDocument.createdAudios.length, 0);
});

test("H.6 video intro delays background music until video completion", async () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            intro: {
                enabled: true,
                mode: "VIDEO",
                assetId: "intro-video",
            },
            audio: {
                enabled: true,
                assetId: "song",
                startPolicy: "AFTER_INTRO",
                volume: 0.7,
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
        logger: { warn() {} },
    });

    controller.start();
    root.children[0].click();
    await Promise.resolve();

    assert.equal(fakeDocument.createdVideos[0].playCalls, 1);
    assert.equal(fakeDocument.createdAudios.length, 0);
    assert.equal(invitation.hidden, true);

    fakeDocument.createdVideos[0].onended();
    await Promise.resolve();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(fakeDocument.createdAudios.length, 1);
    assert.equal(fakeDocument.createdAudios[0].playCalls, 1);
    assert.ok(byClass(root, "experience-audio-control"));
});
