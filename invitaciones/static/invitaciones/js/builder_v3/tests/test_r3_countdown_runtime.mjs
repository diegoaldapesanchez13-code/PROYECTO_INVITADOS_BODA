import assert from "node:assert/strict";
import fs from "node:fs";
import { UniversalRenderer } from "../renderer/renderer.js";

const renderer = Object.create(UniversalRenderer.prototype);
const target = Date.UTC(2030, 0, 3, 4, 5, 6);
const now = Date.UTC(2030, 0, 1, 1, 2, 3);
assert.deepEqual(renderer.calculateCountdownValues(target, now), [2, 3, 3, 3]);
assert.deepEqual(renderer.calculateCountdownValues(now - 1000, now), [0, 0, 0, 0]);
assert.ok(Number.isFinite(renderer.resolveCountdownTimestamp("2030-01-01T12:00")));
assert.ok(Number.isNaN(renderer.resolveCountdownTimestamp("")));

const source = fs.readFileSync(new URL("../renderer/renderer.js", import.meta.url), "utf8");
const preview = fs.readFileSync(new URL("../preview/mobile_preview.js", import.meta.url), "utf8");
assert.match(source, /startCountdownTicker\(\)/);
assert.match(source, /data-r3-countdown-id/);
assert.match(source, /setInterval/);
assert.match(preview, /stopCountdownTicker/);

console.log("✓ Countdown runtime updates dynamic bindings in preview");
