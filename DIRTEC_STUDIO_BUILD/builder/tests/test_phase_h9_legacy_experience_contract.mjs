import assert from "node:assert/strict";
import test from "node:test";

import {
    normalizeExperience,
    validateExperience,
} from "../experience/contract.js";

test("H.9 legacy envelope palettes are valid Experience V4 values", () => {
    const legacyPalettes = [
        "BOSQUE",
        "ROSA",
        "TERRACOTA",
        "AZUL",
        "LAVANDA",
        "DORADO",
        "TINTA_MARFIL",
        "NEGRO_DORADO",
        "VINO_ROSA",
        "SALVIA_PERLA",
        "PERSONALIZADA",
    ];

    for (const palette of legacyPalettes) {
        const experience = normalizeExperience({
            intro: {
                enabled: true,
                mode: "ENVELOPE",
                envelope: {
                    palette,
                    sealAssetId: "db-1",
                },
            },
        });

        assert.equal(experience.intro.envelope.palette, palette);
        assert.equal(validateExperience(experience).valid, true);
    }
});
