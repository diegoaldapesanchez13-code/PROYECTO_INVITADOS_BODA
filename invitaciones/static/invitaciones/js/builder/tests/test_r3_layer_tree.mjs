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

console.log(
    "R3.07.3 Layer Tree tests: OK"
);
