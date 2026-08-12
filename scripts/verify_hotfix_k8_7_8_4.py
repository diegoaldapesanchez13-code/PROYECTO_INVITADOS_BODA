import subprocess
import sys

def run(*args):
    cmd=[sys.executable,"manage.py",*args]
    print("> "+" ".join(cmd))
    subprocess.run(cmd,check=True)

run("check")
run("makemigrations","--check","--dry-run")

# Security changes on current K8 routes.
run(
    "test",
    "eventos.tests_production_hardening_k878",
    "core.tests_tenant_authorization_k",
    "eventos.tests_planner_dashboard_v3",
    "--verbosity=1",
)

# Modernized monolithic contracts that were still producing noise.
run(
    "test",
    "invitaciones.tests",
    "invitaciones.tests_builder_j1_2",
    "invitaciones.tests_dashboard_product_v2",
    "invitaciones.tests_role_redirect_k3",
    "--verbosity=1",
)

# Current source-of-truth suites for guests and package materialization.
run(
    "test",
    "invitaciones.tests_guest_analytics_v2",
    "invitaciones.tests_guest_domain_v2",
    "paquetes.tests_k83",
    "--verbosity=1",
)

print("K.8.7.8.4 authorization + contract cleanup: OK")
print("Siguiente paso obligatorio: python scripts/verify_stable_k8_7_8.py")
