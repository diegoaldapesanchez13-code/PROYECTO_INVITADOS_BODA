import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const builderRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);
const source = fs.readFileSync(
    path.join(builderRoot, "experience", "panel.js"),
    "utf8",
);

test("H.11.2.1 media sliders use local input and commit on change", () => {
    assert.match(
        source,
        /onInput:\s*\(\)\s*=>\s*this\.#updateComposerPreviewFromForm\(\)/,
    );
    assert.match(
        source,
        /input\.addEventListener\("change"/,
    );
    assert.match(
        source,
        /suppressRender:\s*true/,
    );
});

test("H.11.2.1 own experience commits do not recreate panel", () => {
    assert.match(
        source,
        /this\.suppressNextExperienceRender\s*=\s*true/,
    );
    assert.match(
        source,
        /if \(this\.suppressNextExperienceRender\)[\s\S]*?return;/,
    );
});

test("H.11.2.1 device preview changes without this.render", () => {
    const match = source.match(
        /onChange:\s*\(event\)\s*=>\s*\{\s*this\.previewDeviceKey[\s\S]*?\n\s*\},/
    );
    assert.ok(match);
    assert.match(
        match[0],
        /#updateComposerDevicePreview\(\)/,
    );
    assert.doesNotMatch(match[0], /this\.render\(\)/);
});

test("H.11.2.1 focal preset updates form and preview before commit", () => {
    assert.match(source, /#setComposerPosition\(/);
    assert.match(source, /#syncPresetActiveState\(/);
    assert.match(
        source,
        /statusMessage:\s*`Punto focal:/,
    );
});
