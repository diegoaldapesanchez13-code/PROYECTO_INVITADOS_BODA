import assert from "node:assert/strict";
import fs from "node:fs";

const renderer = fs.readFileSync(new URL("../renderer/renderer.js", import.meta.url), "utf8");
const css = fs.readFileSync(new URL("../renderer/renderer.css", import.meta.url), "utf8");
const inspector = fs.readFileSync(new URL("../inspector/index.js", import.meta.url), "utf8");
const registry = fs.readFileSync(new URL("../core/component_registry.js", import.meta.url), "utf8");

assert.match(renderer, /applyVideoContent\(element, node\)/);
assert.match(renderer, /normalizeVideoSource/);
assert.match(renderer, /iframe\.style\.pointerEvents = "none"/);
assert.match(renderer, /video\.style\.pointerEvents = "none"/);
assert.match(css, /\.r3-video-frame/);
assert.match(css, /\.r3-video-fallback/);
assert.match(inspector, /video:\s*videoPanel/);
assert.match(registry, /inspectorPanel:\s*"video"/);

console.log("✓ renderer and inspector expose Video / YouTube contract");
