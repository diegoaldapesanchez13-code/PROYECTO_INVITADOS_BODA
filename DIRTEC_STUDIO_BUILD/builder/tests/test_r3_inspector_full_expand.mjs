import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const css = fs.readFileSync(path.join(here, "../inspector/inspector.css"), "utf8");

assert.match(css, /grid-auto-rows:\s*max-content/);
assert.match(css, /\.r3-inspector-group\s*\{[^}]*overflow:\s*visible/s);
assert.match(css, /\.r3-inspector-group\[open\]\s*\{[^}]*max-height:\s*none/s);
assert.match(css, /\.r3-inspector-group__body\s*\{[^}]*min-height:\s*max-content/s);
assert.doesNotMatch(css, /\.r3-inspector-group\s*\{[^}]*overflow:\s*hidden/s);

console.log("test_r3_inspector_full_expand: ok");
