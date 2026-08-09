import assert from "node:assert/strict";
import { normalizeVideoSource } from "../components/video.js";

const djangoMedia = normalizeVideoSource(
    "/media/editor_invitaciones/assets/video.mp4",
    { sourceType: "library" },
);

assert.equal(djangoMedia.valid, true);
assert.equal(djangoMedia.kind, "direct");
assert.equal(
    djangoMedia.source,
    "/media/editor_invitaciones/assets/video.mp4",
);

const protocolRelative = normalizeVideoSource(
    "//malicious.example/video.mp4",
    { sourceType: "direct" },
);

assert.equal(protocolRelative.valid, false);

console.log("✓ Django MEDIA_URL is a valid persistent video source");
