import assert from "node:assert/strict";
import test from "node:test";
import { adaptR3Panels } from "../frontend/inspector/index.js";

test("R3 Inspector Adapter conserva paneles, tipos y controles", () => {
    const [panel] = adaptR3Panels([{
        id: "typography",
        title: "Tipografía",
        componentTypes: ["TEXT"],
        controls: [{ type: "select", label: "Fuente", path: "style.fontFamily" }],
    }]);
    assert.equal(panel.id, "typography");
    assert.deepEqual(panel.types, ["TEXT"]);
    assert.equal(panel.controls[0].path, "style.fontFamily");
    assert.equal(panel.metadata.source, "builder-r3");
});
