import assert from "node:assert/strict";
import fs from "node:fs";

const renderer = fs.readFileSync(
    new URL("../renderer/renderer.js", import.meta.url),
    "utf8",
);
const css = fs.readFileSync(
    new URL("../assets/library.css", import.meta.url),
    "utf8",
);

assert.match(
    renderer,
    /content\.sourceType === "library"[\s\S]*this\.resolveAssetUrl\(node\)/,
);
assert.match(
    css,
    /\.r3-asset-library__grid[\s\S]*overflow-y:\s*auto/,
);
assert.match(
    css,
    /\.r3-asset-library[\s\S]*grid-template-rows:[\s\S]*minmax\(0,\s*1fr\)/,
);

console.log("✓ library video resolver and independent asset grid scroll");
