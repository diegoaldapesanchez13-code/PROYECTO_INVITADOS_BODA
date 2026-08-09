import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const demoPath = fileURLToPath(
    new URL("../demo_r3_07.js", import.meta.url)
);

test("demo_r3_07.js parses as an ES module", () => {
    const result = spawnSync(
        process.execPath,
        ["--check", demoPath],
        {
            encoding: "utf8",
        }
    );

    assert.equal(
        result.status,
        0,
        result.stderr || result.stdout
    );
});
