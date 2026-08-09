import assert from "node:assert/strict";

import { BuilderState, NODE_TYPES, createEmptyDocument } from "../core/index.js";
import { insertComponent, normalizeVideoSource, normalizeYouTubeSource } from "../components/index.js";

const watch = normalizeYouTubeSource("https://www.youtube.com/watch?v=dQw4w9WgXcQ", {
    autoplay: true,
    loop: true,
    muted: true,
    controls: false,
});
assert.equal(watch.valid, true);
assert.equal(watch.kind, "youtube");
assert.equal(watch.videoId, "dQw4w9WgXcQ");
assert.match(watch.embedUrl, /youtube-nocookie\.com\/embed\/dQw4w9WgXcQ/);
assert.match(watch.embedUrl, /autoplay=1/);
assert.match(watch.embedUrl, /playlist=dQw4w9WgXcQ/);

assert.equal(normalizeVideoSource("https://youtu.be/dQw4w9WgXcQ").valid, true);
assert.equal(normalizeVideoSource("https://www.youtube.com/shorts/dQw4w9WgXcQ").kind, "youtube");
assert.equal(normalizeVideoSource("https://cdn.example.com/video.mp4", { sourceType: "direct" }).kind, "direct");
assert.equal(normalizeVideoSource("javascript:alert(1)", { sourceType: "direct" }).valid, false);
assert.equal(normalizeVideoSource("https://example.com/not-youtube", { sourceType: "youtube" }).valid, false);

const state = new BuilderState(createEmptyDocument());
const section = state.createNode(NODE_TYPES.CANVAS, { name: "Video", height: 900 });
const video = insertComponent({ state, type: NODE_TYPES.VIDEO, selectedNodeId: section.id });
assert.equal(video.type, NODE_TYPES.VIDEO);
assert.equal(video.parentId, section.id);
assert.equal(video.content.sourceType, "youtube");
assert.equal(video.content.controls, true);
assert.equal(video.content.muted, true);
assert.equal(video.style.overflow, "hidden");

console.log("✓ Video / YouTube component normalization and factory");
