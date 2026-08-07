from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CSS=ROOT/"invitaciones/static/invitaciones/css/builder_engine_editor.css"
css=CSS.read_text(encoding="utf-8")
add="""
/* Sprint 10.9.1 — 8 handles universales */
.engine-transform-handle.n { left:50%; top:-7px; transform:translateX(-50%); cursor:ns-resize; }
.engine-transform-handle.s { left:50%; bottom:-7px; transform:translateX(-50%); cursor:ns-resize; }
.engine-transform-handle.e { right:-7px; top:50%; transform:translateY(-50%); cursor:ew-resize; }
.engine-transform-handle.w { left:-7px; top:50%; transform:translateY(-50%); cursor:ew-resize; }
.engine-preview-node { min-width:0; min-height:0; }
.engine-layer-z { font-size:9px; font-weight:600; color:#d2b074; margin-right:5px; }
"""
if "Sprint 10.9.1 — 8 handles universales" not in css: CSS.write_text(css.rstrip()+"\n\n"+add,encoding="utf-8")
BOOT=ROOT/"builder_engine/frontend/integrations/django/editor_bootstrap.js"
b=BOOT.read_text(encoding="utf-8")
old='''            if (path === "name") nodeController.rename(value);
            else nodeController.update(path, value);
            render();'''
new='''            if (path === "name") nodeController.rename(value);
            else if (path === "style.zIndex") nodeController.setZIndex(value);
            else nodeController.update(path, value);
            render();'''
if old in b: BOOT.write_text(b.replace(old,new,1),encoding="utf-8")
TPL=ROOT/"invitaciones/templates/invitaciones/editor_builder_engine.html"
t=TPL.read_text(encoding="utf-8").replace("?v=0.20.1","?v=0.21.0").replace("?v=0.20.0","?v=0.21.0")
TPL.write_text(t,encoding="utf-8")
print("Sprint 10.9.1 aplicado correctamente.")
