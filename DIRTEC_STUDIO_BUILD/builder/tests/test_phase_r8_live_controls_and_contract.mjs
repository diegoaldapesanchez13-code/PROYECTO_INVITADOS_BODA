import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const builderRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);
const read = relative => fs.readFileSync(
    path.join(builderRoot, relative),
    "utf8",
);

test("R8 Inspector live input contract", () => {
    const source = read("inspector/index.js");
    assert.match(source, /liveInputTypes\.has\(definition\.type\)/);
    for (const type of ["text", "textarea", "range", "color"]) {
        assert.match(source, new RegExp(`"${type}"`));
    }
});

test("R8 Experience input commits do not rebuild panel", () => {
    const source = read("experience/panel.js");
    assert.doesNotMatch(
        source,
        /onInput:\s*\(\)\s*=>\s*this\.#commitFromForm\(\),/,
    );
    assert.match(
        source,
        /onInput:\s*\(\)\s*=>\s*this\.#commitFromForm\(\{[\s\S]*?suppressRender:\s*true/,
    );
});

test("R8 RSVP contains no legacy pass/comment authority", () => {
    const panel = read("inspector/panels/rsvp.js");
    const factory = read("components/factory.js");
    for (const forbidden of [
        "showGuestLimit",
        "showComment",
        "maxGuests",
        "confirmedGuests",
        "Pases máximos",
        "Asistentes de ejemplo",
    ]) {
        assert.equal(panel.includes(forbidden), false, forbidden);
        assert.equal(factory.includes(forbidden), false, forbidden);
    }
});

test("R8 AssetLibrary has one implementation", () => {
    const compatibility = read("inspector/library.js");
    assert.match(
        compatibility,
        /export \{ AssetLibrary \} from "\.\.\/assets\/library\.js"/,
    );
    assert.equal(
        compatibility.includes("export class AssetLibrary"),
        false,
    );
});
