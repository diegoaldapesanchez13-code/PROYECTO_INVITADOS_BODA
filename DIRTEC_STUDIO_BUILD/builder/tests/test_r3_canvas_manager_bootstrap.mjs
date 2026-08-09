import assert from "node:assert/strict";

import {
    CanvasManager,
} from "../canvas/canvas_manager.js";

class FakeElement {
    constructor(tagName = "div") {
        this.tagName = tagName;
        this.children = [];
        this.dataset = {};
        this.classList = {
            add() {},
            toggle() {},
        };
    }

    replaceChildren(...children) {
        this.children = children;
    }

    append(...children) {
        this.children.push(...children);
    }

    setAttribute(name, value) {
        this[name] = String(value);
    }

    addEventListener() {}

    querySelectorAll() {
        return [];
    }
}

globalThis.Element = FakeElement;
globalThis.document = {
    createElement(tagName) {
        return new FakeElement(tagName);
    },
};

assert.doesNotThrow(() => {
    new CanvasManager({
        root: new FakeElement(),
        state: {
            document: {
                nodes: [],
            },
            selection: {
                canvasId: null,
            },
            subscribe() {
                return () => {};
            },
        },
        canvas: {
            refreshAfterRender() {},
            select() {},
        },
        renderer: {
            update() {},
            root: new FakeElement(),
        },
    });
});

console.log("CanvasManager bootstrap test: OK");
