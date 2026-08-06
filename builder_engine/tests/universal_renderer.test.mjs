import assert from "node:assert/strict";
import test from "node:test";

import { UniversalRenderer } from "../frontend/renderer/universal_renderer.js";
import { createUniversalRendererFixture } from "../frontend/renderer/universal_fixture.js";

function renderer() {
    return new UniversalRenderer();
}

test("renderiza el mismo árbol visual en EDIT PREVIEW y PUBLIC", () => {
    const document = createUniversalRendererFixture();
    const edit = renderer().renderDocument(document, { mode: "EDIT", device: "mobile" });
    const preview = renderer().renderDocument(document, { mode: "PREVIEW", device: "mobile" });
    const published = renderer().renderDocument(document, { mode: "PUBLIC", device: "mobile" });

    const visual = (result) => result.canvases.map((canvas) => ({
        id: canvas.id,
        width: canvas.width,
        height: canvas.height,
        style: canvas.style,
        children: canvas.children.map(stripMode),
    }));

    assert.deepEqual(visual(edit), visual(preview));
    assert.deepEqual(visual(preview), visual(published));
    assert.equal(edit.metadata.editable, true);
    assert.equal(preview.metadata.interactive, true);
});

test("respeta altura y ancho por dispositivo", () => {
    const document = createUniversalRendererFixture();
    const mobile = renderer().renderDocument(document, { mode: "PREVIEW", device: "mobile" });
    const tablet = renderer().renderDocument(document, { mode: "PREVIEW", device: "tablet" });
    const desktop = renderer().renderDocument(document, { mode: "PREVIEW", device: "desktop" });

    assert.equal(mobile.canvases[0].width, 390);
    assert.equal(mobile.canvases[0].height, 1000);
    assert.equal(tablet.canvases[0].width, 768);
    assert.equal(tablet.canvases[0].height, 900);
    assert.equal(desktop.canvases[0].width, 1180);
    assert.equal(desktop.canvases[0].height, 820);
});

test("resuelve geometría responsive del nodo", () => {
    const document = createUniversalRendererFixture();
    const mobile = renderer().renderDocument(document, { mode: "PREVIEW", device: "mobile" });
    const tablet = renderer().renderDocument(document, { mode: "PREVIEW", device: "tablet" });

    assert.equal(mobile.canvases[0].children[0].style.width, "82%");
    assert.equal(mobile.canvases[0].children[0].style.height, "42%");
    assert.equal(tablet.canvases[0].children[0].style.width, "60%");
    assert.equal(tablet.canvases[0].children[0].style.height, "36%");
});

test("ordena hermanos de atrás hacia delante y normaliza stack", () => {
    const document = createUniversalRendererFixture();
    document.canvases[0].nodes.reverse();

    const result = renderer().renderDocument(document, {
        mode: "PREVIEW",
        device: "mobile",
    });

    assert.deepEqual(
        result.canvases[0].children.map((node) => node.id),
        ["photo", "title", "card"],
    );
    assert.deepEqual(
        result.canvases[0].children.map((node) => node.style.zIndex),
        [1, 2, 3],
    );
});

test("renderiza jerarquía anidada", () => {
    const document = createUniversalRendererFixture();
    const result = renderer().renderDocument(document, {
        mode: "PREVIEW",
        device: "mobile",
    });

    const card = result.canvases[0].children.find((node) => node.id === "card");
    assert.equal(card.children.length, 1);
    assert.equal(card.children[0].id, "card-text");
    assert.equal(card.children[0].style.position, "relative");
});

test("imagen conserva interacción universal", () => {
    const document = createUniversalRendererFixture();
    const edit = renderer().renderDocument(document, { mode: "EDIT" });
    const preview = renderer().renderDocument(document, { mode: "PREVIEW" });

    const editImage = edit.canvases[0].children[0];
    const previewImage = preview.canvases[0].children[0];

    assert.equal(editImage.runtime.actionable, true);
    assert.equal(editImage.runtime.interactionEnabled, false);
    assert.equal(previewImage.runtime.interactionEnabled, true);
    assert.equal(previewImage.attributes.role, "button");
    assert.equal(previewImage.attributes["aria-label"], "Abrir ubicación");
});

test("imagen usa tamaño real del frame", () => {
    const document = createUniversalRendererFixture();
    const result = renderer().renderDocument(document, { mode: "PREVIEW" });
    const image = result.canvases[0].children[0];

    assert.equal(image.tag, "img");
    assert.equal(image.style.width, "82%");
    assert.equal(image.style.height, "42%");
    assert.equal(image.style.objectFit, "cover");
});

test("texto usa etiqueta segura y contenido", () => {
    const document = createUniversalRendererFixture();
    const result = renderer().renderDocument(document, { mode: "PREVIEW" });
    const title = result.canvases[0].children.find((node) => node.id === "title");

    assert.equal(title.tag, "h1");
    assert.equal(title.content, "Fernando & Diego");
    assert.equal(title.style.fontSize, "42px");
});

test("canvas invisible no se renderiza", () => {
    const document = createUniversalRendererFixture();
    document.canvases[0].visible = false;
    const result = renderer().renderDocument(document, { mode: "PUBLIC" });
    assert.equal(result.canvases.length, 0);
});

test("nodo invisible no se renderiza", () => {
    const document = createUniversalRendererFixture();
    document.canvases[0].nodes[0].visible = false;
    const result = renderer().renderDocument(document, { mode: "PUBLIC" });
    assert.equal(result.canvases[0].children.some((node) => node.id === "photo"), false);
});

function stripMode(node) {
    const attributes = { ...node.attributes };
    delete attributes["data-render-mode"];
    return {
        id: node.id,
        type: node.type,
        tag: node.tag,
        attributes,
        style: node.style,
        content: node.content,
        children: node.children.map(stripMode),
    };
}
