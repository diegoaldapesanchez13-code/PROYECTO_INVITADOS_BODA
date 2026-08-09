import assert from "node:assert/strict";

import {
    NODE_TYPES,
    createNode,
} from "../core/index.js";

import {
    INTERACTION_TYPES,
    InteractionEngine,
    googleMapsSearchUrl,
    validateGoogleMapsValue,
} from "../interaction/index.js";

function mapsNode(
    value,
    openInNewTab = false
) {
    return createNode(
        NODE_TYPES.IMAGE,
        {
            interaction: {
                enabled: true,
                action: {
                    type:
                        INTERACTION_TYPES
                            .GOOGLE_MAPS,
                    value,
                    openInNewTab,
                },
            },
        }
    );
}

const calls = [];
const runtime = {
    openUrl(url, options) {
        calls.push({ url, options });
        return {
            executed: true,
            reason: null,
            url,
            openInNewTab:
                options.openInNewTab,
        };
    },
};

const engine = new InteractionEngine({
    runtime,
});

const shortLink = engine.execute(
    mapsNode(
        "https://maps.app.goo.gl/AbCdEf",
        true
    )
);

assert.equal(shortLink.handled, true);
assert.equal(shortLink.status, "executed");
assert.equal(
    shortLink.intent,
    "OPEN_GOOGLE_MAPS"
);
assert.equal(shortLink.payload.source, "url");
assert.equal(
    shortLink.payload.openInNewTab,
    true
);
assert.equal(calls.length, 1);

const coordinates = engine.execute(
    mapsNode("21.122500,-101.683400")
);

assert.equal(coordinates.handled, true);
assert.equal(coordinates.status, "executed");
assert.equal(
    coordinates.payload.source,
    "coordinates"
);
assert.deepEqual(
    coordinates.payload.coordinates,
    {
        latitude: 21.1225,
        longitude: -101.6834,
    }
);
assert.match(
    coordinates.payload.url,
    /^https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=/
);
assert.equal(calls.length, 2);

const googleMapsLink = engine.execute(
    mapsNode(
        "https://www.google.com/maps/place/León,+Gto./@21.12,-101.68,12z"
    )
);

assert.equal(googleMapsLink.handled, true);
assert.equal(googleMapsLink.status, "executed");
assert.equal(calls.length, 3);

for (const invalidValue of [
    "",
    "javascript:alert(1)",
    "https://example.com/maps",
    "91,-101",
    "21,181",
    "no es mapa",
]) {
    const result = engine.execute(
        mapsNode(invalidValue)
    );

    assert.equal(result.handled, false);
    assert.equal(result.status, "invalid");
}

assert.equal(calls.length, 3);
assert.equal(
    validateGoogleMapsValue(
        "https://maps.google.com/?q=León"
    ).valid,
    true
);
assert.equal(
    validateGoogleMapsValue(
        "https://example.com/maps"
    ).valid,
    false
);
assert.equal(
    googleMapsSearchUrl(21, -101),
    "https://www.google.com/maps/search/?api=1&query=21%2C-101"
);

console.log(
    "OK Google Maps executor validates and navigates"
);
