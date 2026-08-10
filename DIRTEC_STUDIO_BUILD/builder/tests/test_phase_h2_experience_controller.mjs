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
        this.listeners.get("click")?.({ type: "click" });
    }
}

class FakeDocument {
    createElement(tagName) {
        return new FakeElement(tagName, this);
    }
}

function documentV4(overrides = {}) {
    return {
        schemaVersion: 4,
        page: { id: "page", name: "Boda", type: "PAGE", settings: {} },
        canvases: [],
        nodes: [],
        assets: [],
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

test("H.2 NONE reveals invitation immediately", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);
    let rendered = false;

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: { enabled: false, mode: "NONE" },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
        renderInvitation() {
            rendered = true;
        },
    });

    const state = controller.start();

    assert.equal(state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(rendered, true);
    assert.equal(invitation.hidden, false);
    assert.equal(invitation.dataset.experienceVisible, "true");
    assert.equal(root.children.length, 0);
});

test("H.2 missing experience preserves current no-intro behavior", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4(),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.2 invalid asset intro falls back to visible invitation", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: {
                    enabled: true,
                    mode: "IMAGE",
                    assetId: "missing",
                },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.2 intro state machine reveals invitation after open gesture", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4({
            experience: {
                intro: {
                    enabled: true,
                    mode: "ENVELOPE",
                    openLabel: "Entrar",
                    transition: {
                        type: "FADE",
                        durationMs: 0,
                    },
                },
            },
        }),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
    });

    controller.start();

    assert.equal(controller.state, EXPERIENCE_STATES.INTRO_PLAYING);
    assert.equal(invitation.hidden, true);
    assert.equal(root.children.length, 1);
    assert.equal(root.children[0].dataset.experienceIntroMode, "ENVELOPE");

    root.children[0].click();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
    assert.equal(root.children.length, 0);
});

test("H.2 controller fails open if invitation render throws", () => {
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const invitation = new FakeElement("article", fakeDocument);

    const controller = new ExperienceController({
        document: documentV4(),
        root,
        invitationElement: invitation,
        domDocument: fakeDocument,
        logger: { warn() {} },
        renderInvitation() {
            throw new Error("render failure");
        },
    });

    controller.start();

    assert.equal(controller.state, EXPERIENCE_STATES.INVITATION_VISIBLE);
    assert.equal(invitation.hidden, false);
});
