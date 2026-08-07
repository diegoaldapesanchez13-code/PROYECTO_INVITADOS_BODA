import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const source = fs.readFileSync(
    path.join(root, "inspector/panels/base.js"),
    "utf8"
);

assert.match(source, /key:\s*"zIndex"/);
assert.match(source, /label:\s*"Capa"/);
assert.match(source, /node\.type\s*!==\s*"SECTION"/);
assert.match(source, /panel Capas/);

console.log("✓ Propiedad Capa disponible para todas las capas visuales");
