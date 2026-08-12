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
    "eventos.tests_client_guests_v3",
    "eventos.tests_client_portal_v3",
    "presupuesto.tests_client_payments_k8741",
    "eventos.tests_provider_portal_v3",
    "eventos.tests_planner_dashboard_v3",
    "eventos.tests_company_dashboard_v3",
    "--verbosity=1",
)
print("K.8.7.6 verification: OK")
