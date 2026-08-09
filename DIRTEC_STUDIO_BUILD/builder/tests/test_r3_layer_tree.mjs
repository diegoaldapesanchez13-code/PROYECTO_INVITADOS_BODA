import assert from "node:assert/strict";

function flattenTree(
    sections,
    childrenOf
) {
    const result = [];

    function visit(node, depth) {
        result.push({
            id: node.id,
            depth,
        });

        for (
            const child
            of childrenOf(node.id)
        ) {
            visit(
                child,
                depth + 1
            );
        }
    }

    for (const section of sections) {
        visit(section, 0);
    }

    return result;
}

const nodes = {
    section: {
        id: "section",
    },
    card: {
        id: "card",
    },
    text: {
        id: "text",
    },
};

const children = {
    section: [nodes.card],
    card: [nodes.text],
    text: [],
};

assert.deepEqual(
    flattenTree(
        [nodes.section],
        (id) => children[id]
    ),
    [
        {
            id: "section",
            depth: 0,
        },
        {
            id: "card",
            depth: 1,
        },
        {
            id: "text",
            depth: 2,
        },
    ]
);

class FakeElement {
    constructor(tagName = "div") {
        this.tagName = tagName;
        this.children = [];
        this.dataset = {};
        this.style = {
            setProperty() {},
        };
        this.classList = {
            add() {},
            toggle() {},
            remove() {},
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

    querySelector() {
        return null;
    }

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

const { LayerTree } = await import("../layers/layer_tree.js");

assert.doesNotThrow(() => {
    const root = new FakeElement();
    const state = {
        document: {
            nodes: [],
        },
        selection: {
            nodeId: null,
        },
        subscribe() {
            return () => {};
        },
    };

    new LayerTree({
        root,
        state,
        canvas: {
            select() {},
        },
    });
});

console.log(
    "R3.07.3 Layer Tree tests: OK"
);
