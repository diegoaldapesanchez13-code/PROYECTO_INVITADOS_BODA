import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");

const base = read("inspector/panels/base.js");
assert.match(base, /key: "zIndex"/);
assert.match(base, /label: "Capa"/);

const countdown = read("inspector/panels/countdown.js");
assert.match(countdown, /key: "columns"/);
assert.match(countdown, /itemMinHeight/);
assert.match(countdown, /itemContentGap/);

const rendererCss = read("renderer/renderer.css");
assert.match(rendererCss, /--r3-countdown-columns/);
assert.match(rendererCss, /height: 100%/);

const canvasCss = read("canvas/canvas.css");
assert.match(canvasCss, /--r3-canvas-height/);
assert.match(canvasCss, /transform: scale\(var\(--r3-canvas-zoom\)\)/);

console.log("test_r3_editor_stabilization: ok");
