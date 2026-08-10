import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const builderRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);
const repoRoot = path.resolve(builderRoot, "..", "..");

function read(file) {
    return fs.readFileSync(file, "utf8");
}

test("H.8 public wraps UniversalRenderer with ExperienceController", () => {
    const source = read(path.join(builderRoot, "public", "public.js"));

    assert.match(source, /import \{ ExperienceController \}/);
    assert.match(source, /new UniversalRenderer/);
    assert.match(source, /new ExperienceController/);
    assert.match(source, /renderInvitation\(\)\s*\{[\s\S]*renderer\.mount\(root, bootstrap\.document\)/);
    assert.match(source, /experience\.start\(\)/);
    assert.match(source, /__DIRTEC_PUBLIC_EXPERIENCE__/);
});

test("H.8 mobile preview only runs experience when requested", () => {
    const source = read(path.join(builderRoot, "preview", "mobile_preview.js"));
    const demo = read(path.join(builderRoot, "demo_r3_07.js"));

    assert.match(source, /open\(options = \{\}\)/);
    assert.match(source, /if \(options\.experience\)/);
    assert.match(source, /renderer\.mount\(surface, this\.state\.document\)/);
    assert.match(source, /restartExperience\(\)/);
    assert.match(demo, /mobilePreview\.open\(\{ experience: true \}\)/);
    assert.match(demo, /mobilePreview\.restartExperience/);
});

test("H.8 templates include versioned experience runtime CSS", () => {
    const editor = read(
        path.join(
            repoRoot,
            "invitaciones",
            "templates",
            "invitaciones",
            "builder",
            "editor.html",
        ),
    );
    const publicTemplate = read(
        path.join(
            repoRoot,
            "invitaciones",
            "templates",
            "invitaciones",
            "builder",
            "public_invitation.html",
        ),
    );

    for (const source of [editor, publicTemplate]) {
        assert.match(
            source,
            /invitaciones\/builder\/experience\/experience\.css' %}\?v={{ builder_build_version\|urlencode }}/,
        );
    }
});
