import assert from "node:assert/strict";
import test from "node:test";
import { BuilderDocumentStorage } from "../persistence/document_storage.js";

function memory() {
    const data = new Map();
    return {
        getItem(k) { return data.get(k) ?? null; },
        setItem(k,v) { data.set(k,v); },
        removeItem(k) { data.delete(k); },
        raw(k) { return data.get(k); },
    };
}

const legacyV3 = {
    schemaVersion: 3,
    page: { id:"page", name:"X", type:"PAGE", settings:{} },
    sections: [{
        id:"c1", type:"SECTION", name:"Canvas", parentId:null,
        sectionId:"c1", order:0, visible:true, locked:false,
        coordinateSpace:"SECTION", x:50,y:50,width:100,height:844,
        style:{},content:{},responsive:{},children:[],
    }],
    nodes: [],
    assets: [],
    responsive: { baseDevice:"desktop", inheritance:{tablet:"desktop",mobile:"tablet"} },
    meta: {},
};

test("storage migrates legacy V3 to native canonical V4", () => {
    const backend = memory();
    backend.setItem("doc", JSON.stringify(legacyV3));
    const storage = new BuilderDocumentStorage({ key:"doc", storage:backend });
    const loaded = storage.load();
    assert.equal(loaded.schemaVersion, 4);
    assert.ok(Array.isArray(loaded.canvases));
    assert.equal(loaded.canvases[0].type, "CANVAS");
    assert.equal(loaded.responsive.baseDevice, "mobile");
});

test("native V4 round trip remains V4", () => {
    const backend = memory();
    const storage = new BuilderDocumentStorage({ key:"doc", storage:backend });
    const v4 = storage.load.bind(storage);
    backend.setItem("doc", JSON.stringify(legacyV3));
    const migrated = storage.load();
    storage.save(migrated);
    const raw = JSON.parse(backend.raw("doc"));
    assert.equal(raw.schemaVersion,4);
    assert.ok(Array.isArray(raw.canvases));
    assert.equal(storage.load().schemaVersion,4);
});
