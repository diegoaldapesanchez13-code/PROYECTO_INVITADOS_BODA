import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");

const html = fs.readFileSync(path.join(root, "demo_r3_07.html"), "utf8");
const demoJs = fs.readFileSync(path.join(root, "demo_r3_07.js"), "utf8");
const canvasCss = fs.readFileSync(path.join(root, "canvas", "canvas.css"), "utf8");
const inspectorCss = fs.readFileSync(path.join(root, "inspector", "inspector.css"), "utf8");
const assetsCss = fs.readFileSync(path.join(root, "assets", "library.css"), "utf8");
const componentsCss = fs.readFileSync(path.join(root, "components", "library.css"), "utf8");
const layersCss = fs.readFileSync(path.join(root, "layers", "layer_tree.css"), "utf8");

assert.match(html, /height:\s*100dvh/);
assert.match(html, /body\s*\{[\s\S]*overflow:\s*hidden/);
assert.match(html, /\.demo-workspace\s*\{[\s\S]*min-height:\s*0;[\s\S]*overflow:\s*hidden/);
assert.match(html, /\.demo-left-panel\s*\{[\s\S]*height:\s*100%;[\s\S]*overflow-y:\s*scroll/);

assert.match(canvasCss, /\.r3-canvas-viewport\s*\{[\s\S]*height:\s*100%;[\s\S]*overflow:\s*auto/);
assert.match(inspectorCss, /\.r3-inspector\s*\{[\s\S]*overflow-y:\s*scroll/);
assert.match(inspectorCss, /\.r3-inspector-header\s*\{[\s\S]*position:\s*sticky/);
assert.match(assetsCss, /\.r3-asset-library__header\s*\{[\s\S]*position:\s*sticky/);
assert.match(componentsCss, /\.r3-component-library__header\s*\{[\s\S]*position:\s*sticky/);
assert.match(layersCss, /\.r3-layer-tree__header\s*\{[\s\S]*position:\s*sticky/);

assert.match(demoJs, /leftPanelScrollPositions/);
assert.match(demoJs, /rememberLeftPanelScroll/);
assert.match(demoJs, /restoreLeftPanelScroll/);

console.log("✓ Layout con scroll independiente validado");
