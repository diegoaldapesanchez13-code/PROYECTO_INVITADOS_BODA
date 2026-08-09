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
const manifest = JSON.parse(
    fs.readFileSync(path.join(builderRoot, "builder.manifest.json"), "utf8"),
);

function walk(dir, predicate, results = []) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const absolute = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            if (entry.name !== "tests") {
                walk(absolute, predicate, results);
            }
            continue;
        }
        if (predicate(absolute)) {
            results.push(absolute);
        }
    }
    return results;
}

function read(file) {
    return fs.readFileSync(file, "utf8");
}

test("F.4 build version is a single deterministic Builder version", () => {
    assert.equal(manifest.schemaVersion, 4);
    assert.equal(manifest.version, "f4-native-v4-freeze");
    assert.match(manifest.version, /^[a-z0-9][a-z0-9.-]*$/);

    const files = [
        ...walk(builderRoot, (file) => [".js", ".html"].includes(path.extname(file))),
        path.join(repoRoot, "invitaciones", "templates", "invitaciones", "builder", "editor.html"),
        path.join(repoRoot, "invitaciones", "templates", "invitaciones", "builder", "public_invitation.html"),
    ];

    const stale = files.filter((file) => read(file).includes("phase-f3-"));
    assert.deepEqual(stale, [], "No debe quedar cache-busting manual phase-f3-*");
});

test("ES module cache queries use the manifest version or bootstrap buildVersion", () => {
    const files = walk(builderRoot, (file) => path.extname(file) === ".js");
    const invalid = [];
    const literalWithQuery = /["'`]([^"'`]*\?v=([^"'`]+))["'`]/g;

    for (const file of files) {
        const source = read(file);
        for (const match of source.matchAll(literalWithQuery)) {
            const url = match[1];
            const version = match[2];
            if (/^https?:\/\//.test(url)) {
                continue;
            }
            if (version === manifest.version) {
                continue;
            }
            if (version === "${encodeURIComponent(buildVersion)}") {
                continue;
            }
            invalid.push(`${path.relative(builderRoot, file)} -> ${url}`);
        }
    }

    assert.deepEqual(invalid, []);
});

test("Django Builder templates version every Builder static asset", () => {
    const templates = [
        path.join(repoRoot, "invitaciones", "templates", "invitaciones", "builder", "editor.html"),
        path.join(repoRoot, "invitaciones", "templates", "invitaciones", "builder", "public_invitation.html"),
    ];
    const unversioned = [];
    const staticRef = /{%\s*static\s+'invitaciones\/builder\/[^']+'\s*%}/g;

    for (const file of templates) {
        const source = read(file);
        for (const match of source.matchAll(staticRef)) {
            const suffix = source.slice(
                match.index + match[0].length,
                match.index + match[0].length + 48,
            );
            if (!suffix.startsWith("?v={{ builder_build_version|urlencode }}")) {
                unversioned.push(`${path.basename(file)} -> ${match[0]}`);
            }
        }
    }

    assert.deepEqual(unversioned, []);
});
