import subprocess
import sys

def run(*args):
    cmd = [sys.executable, "manage.py", *args]
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True)

run("check")
run("makemigrations", "--check", "--dry-run")
run(
    "test",
    "eventos.tests_client_portal_v3",
    "colaboracion.tests_k877_collaboration_ux",
    "--verbosity=1",
)
print("K.8.7.8.1 routing hotfix: OK")
print("Ahora ejecuta: python scripts/verify_stable_k8_7_8.py")
