import subprocess
import sys

def run(*args):
    cmd=[sys.executable,"manage.py",*args]
    print("> "+" ".join(cmd))
    subprocess.run(cmd,check=True)

run("check")
run("makemigrations","--check","--dry-run")

# Contratos modernizados en este hotfix.
run(
    "test",
    "invitaciones.tests",
    "invitaciones.tests_builder_j1_2",
    "invitaciones.tests_dashboard_product_v2",
    "invitaciones.tests_role_redirect_k3",
    "--verbosity=1",
)

# Reconfirma las suites que sustituyen explícitamente los contratos PRE-K8.
run(
    "test",
    "invitaciones.tests_builder_public",
    "invitaciones.tests_builder_django",
    "invitaciones.tests_builder_v4",
    "invitaciones.tests_guest_domain_v2",
    "invitaciones.tests_guest_rsvp_v2",
    "eventos.tests_client_portal_v3",
    "eventos.tests_provider_portal_v3",
    "eventos.tests_client_guests_v3",
    "eventos.tests_dashboard_v3",
    "--verbosity=1",
)

print("K.8.7.8.3 test-contract modernization: OK")
print("Contratos PRE-K8 retirados explícitamente: 52")
print("Siguiente paso obligatorio: python scripts/verify_stable_k8_7_8.py")
