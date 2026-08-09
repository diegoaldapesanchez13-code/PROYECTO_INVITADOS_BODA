import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");

const html = fs.readFileSync(path.join(root, "demo_r3_07.html"), "utf8");
const js = fs.readFileSync(path.join(root, "demo_r3_07.js"), "utf8");
const preview = fs.readFileSync(path.join(root, "preview/mobile_preview.js"), "utf8");
const css = fs.readFileSync(path.join(root, "preview/mobile_preview.css"), "utf8");

assert.match(html, /data-r3-open-preview/);
assert.match(html, /data-r3-preview-surface/);
assert.match(js, /new MobilePreview/);
assert.match(preview, /editable: false/);
assert.match(preview, /iphone_13/);
assert.match(preview, /android/);
assert.match(css, /r3-preview__screen/);

console.log("✓ Mobile Preview Engine contract");
