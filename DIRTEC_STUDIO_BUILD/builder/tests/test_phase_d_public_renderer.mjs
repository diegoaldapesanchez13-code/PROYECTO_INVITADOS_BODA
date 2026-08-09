import assert from "node:assert/strict"; import fs from "node:fs";
const js=fs.readFileSync(new URL("../public/public.js",import.meta.url),"utf8");
assert.match(js,/new UniversalRenderer/); assert.match(js,/editable:\s*false/); assert.match(js,/assetResolver/); assert.match(js,/rsvpProvider/); assert.match(js,/bootstrap\.document/); console.log("✓ PHASE D public runtime uses UniversalRenderer");
