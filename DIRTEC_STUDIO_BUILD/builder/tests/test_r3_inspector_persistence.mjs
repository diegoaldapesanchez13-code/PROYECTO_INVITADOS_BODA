import assert from "node:assert/strict";
import fs from "node:fs";
const source = fs.readFileSync(new URL("../inspector/index.js", import.meta.url), "utf8");
assert.match(source, /groupOpenState/);
assert.match(source, /scrollStateByNode/);
assert.ok(!source.includes("this.render();\n\n        this.onNodeUpdated"));
console.log("test_r3_inspector_persistence: ok");
