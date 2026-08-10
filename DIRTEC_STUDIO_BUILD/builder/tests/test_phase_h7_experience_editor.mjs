import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
    BuilderState,
    NODE_TYPES,
    createEmptyDocument,
    createNode,
} from "../core/index.js";

const builderRoot = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
);
const repoRoot = path.resolve(builderRoot, "..", "..");

function read(relativePath) {
    return fs.readFileSync(path.join(repoRoot, relativePath), "utf8");
}

test("H.7 BuilderState updates experience without disturbing selected node", () => {
    const canvas = createNode(NODE_TYPES.CANVAS, {
        id: "canvas-1",
        children: ["text-1"],
    });
    const text = createNode(NODE_TYPES.TEXT, {
        id: "text-1",
        parentId: "canvas-1",
        canvasId: "canvas-1",
    });
    const state = new BuilderState({
        ...createEmptyDocument(),
        canvases: [canvas],
        nodes: [text],
    });

    state.selectNode("text-1");
    state.updateExperience({
        intro: {
            enabled: true,
            mode: "ENVELOPE",
            openLabel: "Entrar",
            envelope: {
                monogram: "FD",
            },
        },
        audio: {
            enabled: true,
            assetId: "song",
            volume: 0.5,
        },
    });

    assert.equal(state.selection.nodeId, "text-1");
    assert.equal(state.selection.canvasId, "canvas-1");
    assert.equal(state.document.canvases[0].children[0], "text-1");
    assert.equal(state.document.nodes[0].parentId, "canvas-1");
    assert.equal(state.document.experience.intro.mode, "ENVELOPE");
    assert.equal(state.document.experience.audio.assetId, "song");
    assert.equal(state.canUndo, true);
});

test("H.7 editor exposes Experience as a left panel, not Inspector", () => {
    const sourceHtml = fs.readFileSync(
        path.join(builderRoot, "demo_r3_07.html"),
        "utf8",
    );
    const template = read(
        path.join(
            "invitaciones",
            "templates",
            "invitaciones",
            "builder",
            "editor.html",
        ),
    );
    const demoJs = fs.readFileSync(
        path.join(builderRoot, "demo_r3_07.js"),
        "utf8",
    );
    const panelJs = fs.readFileSync(
        path.join(builderRoot, "experience", "panel.js"),
        "utf8",
    );

    for (const html of [sourceHtml, template]) {
        assert.match(html, /data-r3-left-tab="experience"/);
        assert.match(html, /data-r3-left-panel="experience"/);
        assert.match(html, /data-r3-experience/);
    }

    assert.match(
        template,
        /invitaciones\/builder\/experience\/panel\.css' %}\?v={{ builder_build_version\|urlencode }}/,
    );
    assert.match(demoJs, /new ExperiencePanel/);
    assert.doesNotMatch(panelJs, /data-r3-inspector/);
    assert.match(panelJs, /Probar experiencia/);
    assert.match(panelJs, /Reiniciar experiencia/);
});
