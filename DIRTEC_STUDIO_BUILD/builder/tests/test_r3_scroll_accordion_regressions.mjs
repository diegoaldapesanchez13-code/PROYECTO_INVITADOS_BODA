import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const read = (p) => fs.readFileSync(path.join(root, p), "utf8");

const html = read("demo_r3_07.html");
const demo = read("demo_r3_07.js");
const inspectorCss = read("inspector/inspector.css");
const inspectorJs = read("inspector/index.js");
const rendererCss = read("renderer/renderer.css");

assert.match(html, /data-r3-zoom-step="out"/);
assert.match(html, /data-r3-zoom-status/);
assert.match(html, /overflow-y:\s*scroll/);
assert.match(demo, /leftPanelScrollPositions/);
assert.match(demo, /updateZoomStatus/);
assert.match(inspectorCss, /summary::after/);
assert.match(inspectorCss, /scrollbar-color/);
assert.match(inspectorJs, /groupOpenState/);
assert.match(inspectorJs, /scrollStateByNode/);
assert.match(rendererCss, /COMPOSITE COUNTDOWN V1/);

console.log("✓ Scrolls, acordeones, zoom y countdown compuesto preservados");
