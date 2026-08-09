from pathlib import Path
import subprocess, sys

WORKSPACE=Path(__file__).resolve().parents[1]
ROOT=WORKSPACE.parent

def run(cmd,cwd,shell=False):
    print("\n>", cmd if isinstance(cmd,str) else " ".join(map(str,cmd)))
    r=subprocess.run(cmd,cwd=cwd,shell=shell)
    if r.returncode: raise SystemExit(r.returncode)

def main():
    run([sys.executable, WORKSPACE/"scripts/verify_builder_source_parity.py"], ROOT)
    run("node --test builder/tests/*.mjs", WORKSPACE, True)
    run([sys.executable, WORKSPACE/"scripts/build_builder.py"], ROOT)
    run([sys.executable, WORKSPACE/"scripts/verify_builder_build.py"], ROOT)
    run([sys.executable, ROOT/"manage.py", "check"], ROOT)
    print("\nPHASE A.1 GATE OK")

if __name__=="__main__":
    main()
