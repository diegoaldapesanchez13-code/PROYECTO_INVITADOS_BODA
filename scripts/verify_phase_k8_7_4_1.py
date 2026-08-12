import subprocess, sys
def run(*args):
    cmd=[sys.executable,"manage.py",*args]
    print("> "+" ".join(cmd))
    subprocess.run(cmd,check=True)
run("check")
run("makemigrations","--check","--dry-run")
run("showmigrations","presupuesto")
run("test","presupuesto.tests_client_payments_k8741","eventos.tests_client_portal_v3","invitaciones.tests_client_portal_k6","invitaciones.tests_client_portal_layout_k6","eventos.tests_operational_clarity_k8712","eventos.tests_planner_dashboard_v3","eventos.tests_company_dashboard_v3","--verbosity=1")
print("K.8.7.4.1 verification: OK")
