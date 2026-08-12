import subprocess
import sys


def run(*args):
    cmd = [sys.executable, "manage.py", *args]
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True)


run("check")
run("makemigrations", "--check", "--dry-run")
run("showmigrations", "documentos")
run(
    "test",
    "eventos.tests_provider_portal_v3",
    "invitaciones.tests_provider_portal_k7",
    "invitaciones.tests_provider_portal_layout_k7",
    "colaboracion.tests_k84",
    "eventos.tests_operational_clarity_k8712",
    "presupuesto.tests_client_payments_k8741",
    "--verbosity=1",
)
print("K.8.7.5 verification: OK")
