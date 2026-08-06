import fs from "node:fs";
import assert from "node:assert/strict";

const html = fs.readFileSync(new URL("../demo_r3_07.html", import.meta.url), "utf8");
const js = fs.readFileSync(new URL("../demo_r3_07.js", import.meta.url), "utf8");

assert.match(html, /\.demo-left-panel\s*\{[\s\S]*overflow-y:\s*scroll;/);
assert.match(html, /scrollbar-gutter:\s*stable/);
assert.match(js, /return panel \|\| null/);
assert.match(js, /leftPanelScrollPositions/);
console.log("test_r3_left_tabs_scroll: OK");
