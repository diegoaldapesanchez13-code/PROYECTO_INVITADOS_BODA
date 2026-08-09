import assert from "node:assert/strict";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
} from "../core/index.js";

import {
    buildEmbedUrl,
    insertComponent,
    normalizeMapSource,
} from "../components/index.js";

const coordinates = normalizeMapSource("21.1225,-101.6834", { zoom: 17 });
assert.equal(coordinates.valid, true);
assert.equal(coordinates.kind, "coordinates");
assert.match(coordinates.embedUrl, /output=embed/);
assert.match(coordinates.embedUrl, /z=17/);

const query = normalizeMapSource("Templo Expiatorio León Guanajuato");
assert.equal(query.valid, true);
assert.equal(query.kind, "query");
assert.match(query.embedUrl, /q=Templo/);

const iframe = normalizeMapSource(
    '<iframe src="https://www.google.com/maps/embed?pb=test"></iframe>'
);
assert.equal(iframe.valid, true);
assert.equal(iframe.kind, "embed-url");

const short = normalizeMapSource("https://maps.app.goo.gl/example");
assert.equal(short.valid, true);
assert.equal(short.requiresResolution, true);
assert.equal(short.embedUrl, "");

assert.equal(normalizeMapSource("javascript:alert(1)").valid, false);
assert.equal(normalizeMapSource("https://example.com/maps").valid, false);
assert.match(buildEmbedUrl("León", 12), /output=embed/);

const state = new BuilderState(createEmptyDocument());
const section = state.createNode(NODE_TYPES.CANVAS, {
    name: "Ubicación",
    height: 900,
});
const map = insertComponent({
    state,
    type: NODE_TYPES.MAP,
    selectedNodeId: section.id,
});

assert.equal(map.type, NODE_TYPES.MAP);
assert.equal(map.parentId, section.id);
assert.equal(map.content.zoom, 15);
assert.equal(map.style.overflow, "hidden");
assert.equal(map.style.borderRadius, 18);

console.log("✓ Google Maps component, normalization and factory");
