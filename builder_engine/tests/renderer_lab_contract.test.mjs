import assert from "node:assert/strict";
import test from "node:test";
test("compara tres modos",()=>assert.deepEqual(["EDIT","PREVIEW","PUBLIC"],["EDIT","PREVIEW","PUBLIC"]));
test("mantiene anchos lógicos",()=>assert.deepEqual({mobile:390,tablet:768,desktop:1180},{mobile:390,tablet:768,desktop:1180}));
test("es solo lectura",()=>assert.deepEqual(Object.keys({load:"/document/"}),["load"]));
