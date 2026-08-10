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

class FakeDocument {
    createElement(tagName) {
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

function byTag(root, tagName) {
    return collect(root).filter(
        (element) => element.tagName === tagName.toUpperCase(),
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
                id: "jpg",
                type: "IMAGE",
                url: "/media/intro.jpg",
                metadata: { mediaKind: "IMAGE" },
            },
            {
                id: "png-alpha",
                type: "IMAGE",
                url: "/media/intro-alpha.png",
                metadata: { mediaKind: "IMAGE", supportsAlpha: true },
            },
            {
                id: "webp-alpha",
                type: "IMAGE",
                url: "/media/intro-alpha.webp",
                metadata: { mediaKind: "IMAGE", supportsAlpha: true },
            },
            {
                id: "gif",
                type: "IMAGE",
                url: "/media/intro.gif",
                metadata: { mediaKind: "IMAGE", animated: true },
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

function mountIntro(experience) {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);
    const controller = new ExperienceController({
        document: documentV4(experience),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    return { controller, root, invitation };
}

test("H.4 IMAGE intro renders JPG with cover fit", () => {
    const { controller, root, invitation } = mountIntro({
        intro: {
            enabled: true,
            mode: "IMAGE",
            assetId: "jpg",
            fit: "cover",
            backgroundColor: "#112233",
        },
    });

    const overlay = root.children[0];
    const image = byTag(overlay, "img")[0];

    assert.equal(controller.state, EXPERIENCE_STATES.INTRO_PLAYING);
    assert.equal(invitation.hidden, true);
    assert.equal(overlay.dataset.experienceIntroMode, "IMAGE");
    assert.match(overlay.className, /experience-intro--image/);
    assert.equal(overlay.style.backgroundColor, "#112233");
    assert.equal(image.src, "/media/intro.jpg");
    assert.equal(image.style.objectFit, "cover");
});

test("H.4 transparent PNG and WebP remain normal image elements", () => {
    for (const assetId of ["png-alpha", "webp-alpha"]) {
        const { root } = mountIntro({
            intro: {
                enabled: true,
                mode: "IMAGE",
                assetId,
                fit: "contain",
                backgroundColor: "#000000",
            },
        });

        const image = byTag(root.children[0], "img")[0];
        assert.equal(image.tagName, "IMG");
        assert.equal(image.style.objectFit, "contain");
        assert.match(image.src, /\.(png|webp)$/);
    }
});

test("H.4 GIF intro uses animated image asset without decoration semantics", () => {
    const { root } = mountIntro({
        intro: {
            enabled: true,
            mode: "GIF",
            assetId: "gif",
        },
    });

    const overlay = root.children[0];
    const image = byTag(overlay, "img")[0];

    assert.equal(overlay.dataset.experienceIntroMode, "GIF");
    assert.match(overlay.className, /experience-intro--gif/);
    assert.equal(image.tagName, "IMG");
    assert.equal(image.src, "/media/intro.gif");
});

test("H.4 click transition opens the invitation", async () => {
    const { controller, root, invitation } = mountIntro({
        intro: {
            enabled: true,
            mode: "IMAGE",
            assetId: "jpg",
            transition: {
                type: "FADE",
                durationMs: 1,
            },
        },
    });

    const overlay = root.children[0];
    overlay.click();

    assert.equal(overlay.dataset.experienceIntroState, "opening");

    await new Promise((resolve) => setTimeout(resolve, 5));

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.4 image load failure falls back to invitation", () => {
    const { controller, root, invitation } = mountIntro({
        intro: {
            enabled: true,
            mode: "IMAGE",
            assetId: "jpg",
        },
    });

    const image = byTag(root.children[0], "img")[0];
    image.onerror();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});
