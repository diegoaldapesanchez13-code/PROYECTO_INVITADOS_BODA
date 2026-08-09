import assert from "node:assert/strict";

import {
    NODE_TYPES,
    componentElementName,
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
        for (const name of names) {
            this.values.add(name);
        }
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

function findDescendant(node, predicate) {
    for (const child of node.children || []) {
        if (predicate(child)) {
            return child;
        }

        const nested = findDescendant(child, predicate);
        if (nested) {
            return nested;
        }
    }

    return null;
}

globalThis.Element = FakeElement;

assert.notEqual(
    componentElementName(NODE_TYPES.CANVAS),
    "canvas"
);

assert.equal(
    componentElementName(NODE_TYPES.CANVAS),
    "section"
);

const canvas = createNode(
    NODE_TYPES.CANVAS,
    {
        id: "canvas-main",
        name: "Lienzo",
        height: 600,
        children: ["image-main"],
    }
);

const image = createNode(
    NODE_TYPES.IMAGE,
    {
        id: "image-main",
        name: "Portada",
        parentId: canvas.id,
        canvasId: canvas.id,
        width: 80,
        height: 50,
        content: {
            src: "/media/test.png",
        },
    }
);

const documentState = {
    ...createEmptyDocument(),
    canvases: [canvas],
    nodes: [image],
};

const fakeDocument = new FakeDocument();
const root = new FakeElement("main", fakeDocument);
const renderer = new UniversalRenderer({
    editable: true,
    device: "mobile",
});

renderer.mount(root, documentState);

assert.equal(root.children.length, 1);

const canvasElement = root.children[0];
assert.equal(canvasElement.tagName, "SECTION");
assert.equal(
    canvasElement.classList.contains("r3-node--canvas"),
    true
);

const renderedChild = findDescendant(
    canvasElement,
    (element) => element.dataset?.r3NodeId === image.id
);

assert.ok(renderedChild);
assert.equal(renderedChild.tagName, "IMG");

console.log("R3 renderer CANVAS container test: OK");
