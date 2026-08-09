import subprocess,sys
steps=[
 [sys.executable,"manage.py","check"],
 [sys.executable,"manage.py","test","invitaciones.tests_builder_public"],
 [sys.executable,"DIRTEC_STUDIO_BUILD/scripts/build_builder.py"],
 [sys.executable,"DIRTEC_STUDIO_BUILD/scripts/verify_builder_build.py"],
]
for cmd in steps:
 print("\n>"," ".join(cmd)); r=subprocess.run(cmd)
 if r.returncode: raise SystemExit(r.returncode)
r=subprocess.run("node --test builder/tests/*.mjs",cwd="DIRTEC_STUDIO_BUILD",shell=True)
if r.returncode: raise SystemExit(r.returncode)
print("\nPHASE D GATE OK")
