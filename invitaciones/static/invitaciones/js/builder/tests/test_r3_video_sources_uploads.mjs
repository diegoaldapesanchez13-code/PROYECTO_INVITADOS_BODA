import assert from "node:assert/strict";
import { normalizeVideoSource } from "../components/video.js";

const youtube = normalizeVideoSource("https://youtu.be/dQw4w9WgXcQ", {
    sourceType: "youtube",
    controls: true,
});
assert.equal(youtube.valid, true);
assert.equal(youtube.kind, "youtube");
assert.match(youtube.embedUrl, /youtube-nocookie\.com\/embed\/dQw4w9WgXcQ/);

const library = normalizeVideoSource("blob:https://example.com/video-id", {
    sourceType: "library",
});
assert.equal(library.valid, true);
assert.equal(library.kind, "direct");

const uploaded = normalizeVideoSource("data:video/mp4;base64,AAAA", {
    sourceType: "library",
});
assert.equal(uploaded.valid, true);
assert.equal(uploaded.kind, "direct");

console.log("✓ video sources: YouTube iframe y biblioteca local");
