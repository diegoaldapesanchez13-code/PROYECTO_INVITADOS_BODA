import assert from "node:assert/strict";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";

class FakeElement {
    constructor(tagName = "div", rect = {}) {
        this.tagName = tagName;
        this.children = [];
        this.dataset = {};
        this.hidden = false;
        this.isConnected = true;
        this.listeners = new Map();
        this.rect = {
            left: 0,
            top: 0,
            width: 100,
            height: 50,
            ...rect,
        };
        this.style = {
            setProperty: (name, value) => {
                this.style[name] = value;
            },
        };
        this.classList = {
            add() {},
            remove() {},
            toggle() {},
        };
    }

    append(...children) {
        this.children.push(...children);
    }

    remove() {
        this.isConnected = false;
    }

    setAttribute(name, value) {
        this[name] = String(value);
    }

    addEventListener(type, listener) {
        this.listeners.set(type, listener);
    }

    removeEventListener(type) {
        this.listeners.delete(type);
    }

    querySelector(selector) {
        if (selector === "[data-r3-selection-label]") {
            return this.children.find((child) => child.dataset?.r3SelectionLabel) || null;
        }

        return null;
    }

    querySelectorAll(selector) {
        if (selector === "[data-r3-resize-handle]") {
            return this.children.filter((child) => child.dataset?.r3ResizeHandle);
        }

        return [];
    }

    getBoundingClientRect() {
        return this.rect;
    }
}

class FakeSurface extends FakeElement {
    constructor() {
        super("section");
        this.currentNodeElement = null;
    }

    querySelector(selector) {
        if (selector.startsWith("[data-r3-node-id=")) {
            return this.currentNodeElement;
        }

        return super.querySelector(selector);
    }

    contains(element) {
        return element === this.currentNodeElement;
    }
}

globalThis.Element = FakeElement;
globalThis.document = {
    createElement(tagName) {
        return new FakeElement(tagName);
    },
};
globalThis.window = {
    addEventListener() {},
    removeEventListener() {},
};
globalThis.requestAnimationFrame = (callback) => {
    callback();
    return 1;
};

const {
    CanvasSelectionEngine,
} = await import("../canvas/selection.js");

const state = new BuilderState(createEmptyDocument());
const canvasNode = state.createNode(NODE_TYPES.CANVAS);
const textNode = state.createNode(NODE_TYPES.TEXT, {
    parentId: canvasNode.id,
    canvasId: canvasNode.id,
    content: {
        text: "Texto inicial",
        tag: "p",
    },
});

let selectionEvents = 0;
let logicalSelectionChanges = 0;
let inspectorRenderCount = 0;

state.subscribe((event) => {
    if (event.type === "selection:change") {
        selectionEvents += 1;
    }
});

const viewport = new FakeElement("div");
const zoomLayer = new FakeElement("div");
const surface = new FakeSurface();
const overlayLayer = new FakeElement("div", {
    left: 5,
    top: 10,
    width: 390,
    height: 844,
});

const firstElement = new FakeElement("p", {
    left: 25,
    top: 40,
    width: 120,
    height: 30,
});
firstElement.dataset.r3NodeId = textNode.id;
surface.currentNodeElement = firstElement;

const selection = new CanvasSelectionEngine({
    state,
    renderer: {},
    viewport,
    zoomLayer,
    surface,
    overlayLayer,
    onSelectionChange() {
        logicalSelectionChanges += 1;
        inspectorRenderCount += 1;
    },
});

selection.select(textNode.id);

assert.equal(selectionEvents, 1);
assert.equal(logicalSelectionChanges, 1);
assert.equal(inspectorRenderCount, 1);
assert.equal(selection.selectedElement, firstElement);
assert.equal(selection.overlay.hidden, false);

state.updateNode(textNode.id, {
    content: {
        text: "Texto editado en vivo",
        tag: "p",
    },
});

const secondElement = new FakeElement("p", {
    left: 45,
    top: 70,
    width: 160,
    height: 36,
});
secondElement.dataset.r3NodeId = textNode.id;
surface.currentNodeElement = secondElement;

selection.select(textNode.id);

assert.equal(selectionEvents, 1);
assert.equal(logicalSelectionChanges, 1);
assert.equal(inspectorRenderCount, 1);
assert.equal(selection.selectedElement, secondElement);
assert.equal(selection.overlay.hidden, false);
assert.equal(selection.overlay.style.left, "40px");
assert.equal(selection.overlay.style.top, "60px");
assert.equal(selection.overlay.style.width, "160px");
assert.equal(selection.overlay.style.height, "36px");

console.log("test_r3_selection_same_node_refresh: ok");
