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
    "eventos.tests_client_guests_v3",
    "eventos.tests_operational_clarity_k8712",
    "--verbosity=1",
)
print("K.8.7.6.1 verification: OK")
