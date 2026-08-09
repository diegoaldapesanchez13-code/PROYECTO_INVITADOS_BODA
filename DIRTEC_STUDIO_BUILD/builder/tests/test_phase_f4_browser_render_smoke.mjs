import assert from "node:assert/strict";
import test from "node:test";

import {
    NODE_TYPES,
    createEmptyDocument,
    createNode,
} from "../core/index.js";

import {
    UniversalRenderer,
} from "../renderer/renderer.js";

class FakeStyle {
    constructor() {
        this.values = new Map();
    }

    setProperty(name, value) {
        this.values.set(name, String(value));
    }
}

class FakeClassList {
    constructor() {
        this.values = new Set();
    }

    add(...names) {
        names.forEach((name) => this.values.add(name));
    }

    contains(name) {
        return this.values.has(name);
    }
}

class FakeElement {
    constructor(tagName = "div", ownerDocument = null) {
        this.tagName = String(tagName).toUpperCase();
        this.ownerDocument = ownerDocument;
        this.children = [];
        this.dataset = {};
        this.style = new FakeStyle();
        this.classList = new FakeClassList();
        this.attributes = new Map();
        this.hidden = false;
        this.textContent = "";
    }

    replaceChildren(...children) {
        this.children = [];
        this.append(...children);
    }

    append(...children) {
        for (const child of children) {
            if (child?.isFragment) {
                this.children.push(...child.children);
            } else {
                this.children.push(child);
            }
        }
    }

    setAttribute(name, value) {
        this.attributes.set(name, String(value));
    }

    addEventListener() {}
}

class FakeDocument {
    createElement(tagName) {
        return new FakeElement(tagName, this);
    }

    createDocumentFragment() {
        const fragment = new FakeElement("#fragment", this);
        fragment.isFragment = true;
        return fragment;
    }
}

function collect(node, result = []) {
    for (const child of node.children || []) {
        result.push(child);
        collect(child, result);
    }
    return result;
}

function byNodeId(root) {
    return new Map(
        collect(root)
            .filter((element) => element.dataset?.r3NodeId)
            .map((element) => [element.dataset.r3NodeId, element]),
    );
}

globalThis.Element = FakeElement;

test("F.4 browser smoke renders a realistic V4 tree as non-empty DOM", () => {
    const canvasOne = createNode(NODE_TYPES.CANVAS, {
        id: "canvas-one",
        name: "Portada",
        height: 844,
        order: 0,
        children: ["background-one", "card-one", "decor-one"],
    });
    const canvasTwo = createNode(NODE_TYPES.CANVAS, {
        id: "canvas-two",
        name: "Ceremonia",
        height: 960,
        order: 1,
        children: ["image-two", "button-two"],
    });
    const background = createNode(NODE_TYPES.BACKGROUND, {
        id: "background-one",
        parentId: canvasOne.id,
        canvasId: canvasOne.id,
        content: { src: "/media/background.webp" },
    });
    const card = createNode(NODE_TYPES.CARD, {
        id: "card-one",
        parentId: canvasOne.id,
        canvasId: canvasOne.id,
        children: ["text-one", "image-one"],
    });
    const text = createNode(NODE_TYPES.TEXT, {
        id: "text-one",
        parentId: card.id,
        canvasId: canvasOne.id,
        content: { text: "Fernanda & Diego" },
    });
    const image = createNode(NODE_TYPES.IMAGE, {
        id: "image-one",
        parentId: card.id,
        canvasId: canvasOne.id,
        content: { src: "/media/photo.jpg" },
    });
    const decoration = createNode(NODE_TYPES.DECORATION, {
        id: "decor-one",
        parentId: canvasOne.id,
        canvasId: canvasOne.id,
        content: { src: "/media/animado.gif" },
    });
    const secondImage = createNode(NODE_TYPES.IMAGE, {
        id: "image-two",
        parentId: canvasTwo.id,
        canvasId: canvasTwo.id,
        content: { src: "/media/map.webp" },
    });
    const button = createNode(NODE_TYPES.BUTTON, {
        id: "button-two",
        parentId: canvasTwo.id,
        canvasId: canvasTwo.id,
        content: { label: "Ir ubicacion", href: "#" },
    });

    const documentState = {
        ...createEmptyDocument(),
        canvases: [canvasOne, canvasTwo],
        nodes: [
            background,
            card,
            text,
            image,
            decoration,
            secondImage,
            button,
        ],
    };
    const fakeDocument = new FakeDocument();
    const root = new FakeElement("main", fakeDocument);
    const renderer = new UniversalRenderer({
        editable: true,
        device: "mobile",
    });

    renderer.mount(root, documentState);

    assert.equal(root.children.length, 2);
    assert.equal(root.children[0].tagName, "SECTION");
    assert.equal(root.children[1].tagName, "SECTION");
    assert.equal(root.children[0].classList.contains("r3-node--canvas"), true);
    assert.equal(root.children[1].classList.contains("r3-node--canvas"), true);

    const elements = byNodeId(root);
    for (const node of [canvasOne, canvasTwo, background, card, text, image, decoration, secondImage, button]) {
        assert.ok(elements.has(node.id), `No se renderizo ${node.id}`);
    }

    assert.equal(elements.get("text-one").tagName, "P");
    assert.equal(elements.get("image-one").tagName, "IMG");
    assert.equal(elements.get("decor-one").tagName, "IMG");
    assert.equal(elements.get("button-two").tagName, "A");

    const cardDescendants = byNodeId(elements.get("card-one"));
    assert.ok(cardDescendants.has("text-one"));
    assert.ok(cardDescendants.has("image-one"));
});
