import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const css = fs.readFileSync(path.join(root, "assets", "library.css"), "utf8");
const js = fs.readFileSync(path.join(root, "assets", "library.js"), "utf8");
const html = fs.readFileSync(path.join(root, "demo_r3_07.html"), "utf8");
const djangoEditor = fs.readFileSync(
    path.resolve(root, "..", "..", "invitaciones", "templates", "invitaciones", "builder", "editor.html"),
    "utf8",
);

assert.match(
    html,
    /\.demo-left-panel\[data-r3-left-panel="assets"\]\s*\{[\s\S]*overflow:\s*hidden/,
    "Assets tab must not compete with the resource-grid vertical scroll",
);
assert.match(
    djangoEditor,
    /\.demo-left-panel\[data-r3-left-panel="assets"\]\s*\{[\s\S]*overflow:\s*hidden/,
    "Django editor must use the same single-scroll Assets contract",
);
assert.match(
    css,
    /\.r3-asset-library__grid\s*\{[\s\S]*grid-auto-rows:\s*max-content;[\s\S]*overflow-y:\s*auto/,
    "Resource grid owns the vertical scroll and keeps content-sized cards",
);
assert.match(
    css,
    /\.r3-asset-card__preview\s*\{[\s\S]*min-height:\s*92px;[\s\S]*aspect-ratio:\s*4\s*\/\s*3/,
    "Asset previews must remain legible",
);
assert.match(js, /r3-asset-card__inspect/);
assert.match(js, /#openAssetDetail\(asset\)/);
assert.match(js, /r3-asset-detail__media/);
assert.match(js, /asset\.mimeType[\s\S]*startsWith\("audio\/"\)[\s\S]*r3-asset-card__audio-preview/);
assert.match(js, /\.mp3/);

console.log("✓ H.11.1 Asset Library workspace: scroll, cards, detail preview and audio preview");
