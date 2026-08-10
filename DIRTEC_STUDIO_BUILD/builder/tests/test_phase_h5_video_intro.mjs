import assert from "node:assert/strict";
import test from "node:test";

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

class FakeVideoElement extends FakeElement {
    constructor(ownerDocument, options = {}) {
        super("video", ownerDocument);
        this.playCalls = 0;
        this.pauseCalls = 0;
        this.rejectPlay = Boolean(options.rejectPlay);
    }

    play() {
        this.playCalls += 1;
        return this.rejectPlay
            ? Promise.reject(new Error("blocked"))
            : Promise.resolve();
    }

    pause() {
        this.pauseCalls += 1;
    }
}

class FakeDocument {
    constructor(options = {}) {
        this.options = options;
        this.createdVideos = [];
    }

    createElement(tagName) {
        if (String(tagName).toLowerCase() === "video") {
            const video = new FakeVideoElement(this, this.options);
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
                id: "intro-video",
                type: "VIDEO",
                url: "/media/intro.mp4",
            },
            {
                id: "poster",
                type: "IMAGE",
                url: "/media/poster.webp",
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

function mountVideo(experience, options = {}) {
    const fakeDocument = new FakeDocument(options);
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);
    const controller = new ExperienceController({
        document: documentV4(experience),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
        logger: { warn() {} },
    });

    controller.start();

    return {
        controller,
        root,
        invitation,
        video: fakeDocument.createdVideos[0],
    };
}

test("H.5 video intro renders poster and waits for user gesture", () => {
    const { controller, root, invitation, video } = mountVideo({
        intro: {
            enabled: true,
            mode: "VIDEO",
            assetId: "intro-video",
            posterAssetId: "poster",
            fit: "contain",
            video: {
                controls: true,
                muted: true,
                playsInline: true,
            },
        },
    });

    const overlay = root.children[0];

    assert.equal(controller.state, EXPERIENCE_STATES.INTRO_PLAYING);
    assert.equal(invitation.hidden, true);
    assert.equal(overlay.dataset.experienceIntroMode, "VIDEO");
    assert.equal(video.src, "/media/intro.mp4");
    assert.equal(video.poster, "/media/poster.webp");
    assert.equal(video.controls, true);
    assert.equal(video.muted, true);
    assert.equal(video.playsInline, true);
    assert.equal(video.attributes.has("playsinline"), true);
    assert.equal(video.loop, false);
    assert.equal(video.style.objectFit, "contain");
    assert.equal(video.playCalls, 0);
});

test("H.5 video click plays and ended reveals invitation", async () => {
    const { controller, root, invitation, video } = mountVideo({
        intro: {
            enabled: true,
            mode: "VIDEO",
            assetId: "intro-video",
        },
    });

    root.children[0].click();
    await Promise.resolve();

    assert.equal(video.playCalls, 1);
    assert.equal(root.children[0].dataset.experienceIntroState, "playing");
    assert.equal(invitation.hidden, true);

    video.onended();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.5 skip stops video and opens invitation", async () => {
    const { controller, root, invitation, video } = mountVideo({
        intro: {
            enabled: true,
            mode: "VIDEO",
            assetId: "intro-video",
            allowSkip: true,
        },
    });

    root.children[0].click();
    await Promise.resolve();

    byClass(root, "experience-intro__skip").click();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(video.pauseCalls, 1);
});

test("H.5 play rejection fails open", async () => {
    const { controller, root, invitation, video } = mountVideo(
        {
            intro: {
                enabled: true,
                mode: "VIDEO",
                assetId: "intro-video",
            },
        },
        { rejectPlay: true },
    );

    root.children[0].click();
    await Promise.resolve();
    await Promise.resolve();

    assert.equal(video.playCalls, 1);
    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.5 missing video asset never blocks invitation", () => {
    const { controller, root, invitation } = mountVideo({
        intro: {
            enabled: true,
            mode: "VIDEO",
            assetId: "missing-video",
        },
    });

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});
