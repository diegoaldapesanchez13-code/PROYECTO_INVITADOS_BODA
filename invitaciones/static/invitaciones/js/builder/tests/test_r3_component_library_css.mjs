import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const componentCss = await readFile(
    new URL("../components/library.css", import.meta.url),
    "utf8"
);
const rendererCss = await readFile(
    new URL("../renderer/renderer.css", import.meta.url),
    "utf8"
);

assert.match(componentCss, /\.r3-component-library__grid/);
assert.match(componentCss, /grid-template-columns:\s*repeat\(2/);
assert.match(rendererCss, /\.r3-node--button[\s\S]*var\(--r3-padding-y/);

console.log("✓ estilos de Componentes y Botón integrados");
