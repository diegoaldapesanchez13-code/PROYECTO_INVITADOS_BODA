import subprocess
import sys

def run(*args):
    cmd = [sys.executable, "manage.py", *args]
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True)

run("check")
run("makemigrations", "--check", "--dry-run")

# Focus the regression exactly where K.8.7.8 hardening changed behavior.
run(
    "test",
    "colaboracion.tests_k877_collaboration_ux",
    "--verbosity=1",
)

# Re-run Client Portal because it shares the service workspace.
run(
    "test",
    "eventos.tests_client_portal_v3",
    "--verbosity=1",
)

print("K.8.7.8.2 transaction hotfix: OK")
print("Siguiente paso obligatorio: python scripts/verify_stable_k8_7_8.py")
