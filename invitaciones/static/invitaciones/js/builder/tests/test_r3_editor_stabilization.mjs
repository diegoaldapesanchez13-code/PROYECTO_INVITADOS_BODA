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
assert.match(countdown, /Edición por capas/);
assert.match(countdown, /content\.values\.0/);
assert.match(countdown, /content\.targetDate/);

const rendererCss = read("renderer/renderer.css");
assert.match(rendererCss, /COMPOSITE COUNTDOWN V1/);
assert.match(rendererCss, /\.r3-node--countdown/);

const canvasCss = read("canvas/canvas.css");
assert.match(canvasCss, /--r3-canvas-zoom/);
assert.match(canvasCss, /transform:\s*[\s\S]*scale\([\s\S]*var\(--r3-canvas-zoom\)/);

console.log("test_r3_editor_stabilization: ok");
