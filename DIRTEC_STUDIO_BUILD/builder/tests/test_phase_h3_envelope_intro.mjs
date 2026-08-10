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

function byClass(root, className) {
    return collect(root).filter((element) =>
        String(element.className || "")
            .split(/\s+/)
            .includes(className)
    );
}

function documentV4(overrides = {}) {
    return {
        schemaVersion: 4,
        page: { id: "page", name: "Boda", type: "PAGE", settings: {} },
        canvases: [
            {
                id: "canvas-1",
                type: "CANVAS",
                parentId: null,
                canvasId: "canvas-1",
                children: [],
            },
        ],
        nodes: [],
        assets: [
            {
                id: "envelope-bg",
                type: "IMAGE",
                url: "/media/envelope-bg.webp",
            },
            {
                id: "seal",
                type: "IMAGE",
                url: "/media/seal.png",
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

test("H.3 envelope renders outside canvases with configured assets", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: {
                    enabled: true,
                    mode: "ENVELOPE",
                    openLabel: "Abrir",
                    envelope: {
                        backgroundAssetId: "envelope-bg",
                        sealAssetId: "seal",
                        monogram: "F&D",
                        message: "Nos casamos",
                    },
                },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    const overlay = root.children[0];
    assert.equal(controller.state, EXPERIENCE_STATES.INTRO_PLAYING);
    assert.equal(invitation.hidden, true);
    assert.equal(overlay.dataset.experienceIntroMode, "ENVELOPE");
    assert.match(overlay.className, /experience-intro--envelope/);
    assert.match(overlay.style.backgroundImage, /envelope-bg\.webp/);
    assert.equal(byClass(overlay, "experience-envelope").length, 1);
    assert.equal(byClass(overlay, "experience-envelope__seal").length, 1);
    assert.equal(byClass(overlay, "experience-envelope__monogram")[0].textContent, "F&D");
    assert.equal(byClass(overlay, "experience-envelope__message")[0].textContent, "Nos casamos");
});

test("H.3 envelope missing assets uses fallback and still opens", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: {
                    enabled: true,
                    mode: "ENVELOPE",
                    transition: {
                        type: "FADE",
                        durationMs: 0,
                    },
                    envelope: {
                        backgroundAssetId: "missing-bg",
                        sealAssetId: "missing-seal",
                        monogram: "FD",
                    },
                },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    const overlay = root.children[0];
    assert.equal(byClass(overlay, "experience-envelope__seal-fallback").length, 1);

    overlay.click();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.3 envelope marks opening state before transition completes", async () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: {
                    enabled: true,
                    mode: "ENVELOPE",
                    transition: {
                        type: "FADE",
                        durationMs: 1,
                    },
                },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();
    const overlay = root.children[0];

    overlay.click();

    assert.equal(overlay.dataset.experienceIntroState, "opening");
    assert.match(overlay.className, /experience-intro--opening/);

    await new Promise((resolve) => setTimeout(resolve, 5));

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});
