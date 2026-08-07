import assert from "node:assert/strict";
import fs from "node:fs";

const renderer = fs.readFileSync(
    new URL("../renderer/renderer.js", import.meta.url),
    "utf8"
);
const css = fs.readFileSync(
    new URL("../renderer/renderer.css", import.meta.url),
    "utf8"
);
const inspector = fs.readFileSync(
    new URL("../inspector/index.js", import.meta.url),
    "utf8"
);

assert.match(renderer, /applyMapContent\(element, node\)/);
assert.match(renderer, /iframe\.style\.pointerEvents = "none"/);
assert.match(renderer, /normalizeMapSource/);
assert.match(css, /\.r3-map-frame/);
assert.match(css, /\.r3-map-fallback/);
assert.match(inspector, /map:\s*mapPanel/);

console.log("✓ renderer and inspector expose Google Maps contract");
