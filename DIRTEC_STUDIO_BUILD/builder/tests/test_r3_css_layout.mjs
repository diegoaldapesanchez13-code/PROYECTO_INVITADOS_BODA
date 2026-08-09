import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(
    fileURLToPath(import.meta.url)
);

const cssPath = path.resolve(
    here,
    "../renderer/renderer.css"
);

const css = fs.readFileSync(
    cssPath,
    "utf8"
);

function declarationsFor(selectorStart) {
    const start = css.indexOf(selectorStart);

    assert.notEqual(
        start,
        -1,
        `No existe ${selectorStart}`
    );

    const open = css.indexOf("{", start);
    const close = css.indexOf("}", open);

    assert.ok(open > start && close > open);

    return css.slice(open + 1, close);
}

assert.match(
    declarationsFor(
        ".r3-layout-absolute,"
    ),
    /position:\s*absolute;/
);

assert.doesNotMatch(
    declarationsFor(
        ".r3-node--container,"
    ),
    /position\s*:/
);

assert.match(
    declarationsFor(
        ".r3-node--canvas {"
    ),
    /position:\s*relative;/
);

console.log(
    "R3.06.4 CSS layout ownership tests: OK"
);
