import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
    normalizeExperience,
    validateExperience,
} from "../experience/contract.js";
import { ExperienceController } from "../experience/controller.js";

const builderRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);

class FakeElement {
    constructor(tagName = "div") {
        this.tagName = String(tagName).toUpperCase();
        this.children = [];
        this.dataset = {};
        this.attributes = new Map();
        this.listeners = new Map();
        this.style = {};
        this.hidden = false;
        this.parentNode = null;
        this.className = "";
        this.textContent = "";
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
        if (this.parentNode) {
            this.parentNode.children =
                this.parentNode.children.filter(
                    (child) => child !== this,
                );
        }
        this.parentNode = null;
    }

    setAttribute(name, value) {
        this.attributes.set(name, String(value));
    }

    addEventListener(name, listener) {
        this.listeners.set(name, listener);
    }

    pause() {}
    play() { return Promise.resolve(); }
}

class FakeDocument {
    createElement(tagName) {
        return new FakeElement(tagName);
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
    return collect(root).find(
        (node) => node.tagName === tagName.toUpperCase(),
    );
}

function documentV4(mode, assetId) {
    return {
        schemaVersion: 4,
        page: { id: "page", name: "Test", type: "PAGE", settings: {} },
        canvases: [],
        nodes: [],
        assets: [
            { id: "image", type: "IMAGE", url: "/media/intro.webp" },
            { id: "video", type: "VIDEO", url: "/media/intro.mp4" },
        ],
        responsive: {
            baseDevice: "mobile",
            inheritance: {
                tablet: "mobile",
                desktop: "tablet",
            },
        },
        meta: {},
        experience: {
            intro: {
                enabled: true,
                mode,
                assetId,
                fit: "cover",
                mediaPosition: { x: 25, y: 70 },
                mediaScale: 1.35,
            },
        },
    };
}

test("H.11.2 contract defaults mobile media placement safely", () => {
    const experience = normalizeExperience({
        intro: {
            enabled: true,
            mode: "IMAGE",
        },
    });

    assert.deepEqual(
        experience.intro.mediaPosition,
        { x: 50, y: 50 },
    );
    assert.equal(experience.intro.mediaScale, 1);
    assert.equal(validateExperience(experience).valid, true);
});

test("H.11.2 contract clamps position and scale", () => {
    const experience = normalizeExperience({
        intro: {
            enabled: true,
            mode: "VIDEO",
            mediaPosition: {
                x: -30,
                y: 130,
            },
            mediaScale: 4,
        },
    });

    assert.deepEqual(
        experience.intro.mediaPosition,
        { x: 0, y: 100 },
    );
    assert.equal(experience.intro.mediaScale, 2);
});

test("H.11.2 IMAGE runtime applies focal position and scale", () => {
    const domDocument = new FakeDocument();
    const root = new FakeElement("main");
    const invitation = new FakeElement("article");
    const controller = new ExperienceController({
        document: documentV4("IMAGE", "image"),
        root,
        invitationElement: invitation,
        domDocument,
    });

    controller.start();

    const image = byTag(root, "img");
    assert.equal(image.style.objectFit, "cover");
    assert.equal(image.style.objectPosition, "25% 70%");
    assert.equal(image.style.transform, "scale(1.35)");
    assert.equal(image.style.transformOrigin, "25% 70%");
});

test("H.11.2 VIDEO runtime uses the same placement contract", () => {
    const domDocument = new FakeDocument();
    const root = new FakeElement("main");
    const invitation = new FakeElement("article");
    const controller = new ExperienceController({
        document: documentV4("VIDEO", "video"),
        root,
        invitationElement: invitation,
        domDocument,
    });

    controller.start();

    const video = byTag(root, "video");
    assert.equal(video.style.objectPosition, "25% 70%");
    assert.equal(video.style.transform, "scale(1.35)");
    assert.equal(video.style.transformOrigin, "25% 70%");
});

test("H.11.2 editor exposes mobile composer without touching node Inspector", () => {
    const panel = fs.readFileSync(
        path.join(builderRoot, "experience", "panel.js"),
        "utf8",
    );
    const css = fs.readFileSync(
        path.join(builderRoot, "experience", "panel.css"),
        "utf8",
    );

    assert.match(panel, /Encuadre móvil/);
    assert.match(panel, /intro\.mediaPosition\.x/);
    assert.match(panel, /intro\.mediaPosition\.y/);
    assert.match(panel, /intro\.mediaScale/);
    assert.match(panel, /iPhone 13 \/ 14/);
    assert.match(panel, /iPhone SE/);
    assert.match(panel, /Android/);
    assert.match(panel, /MEDIA_POSITION_PRESETS/);
    assert.doesNotMatch(panel, /data-r3-inspector/);

    assert.match(css, /\.experience-media-composer__preview/);
    assert.match(css, /\.experience-media-composer__preset-grid/);
});
