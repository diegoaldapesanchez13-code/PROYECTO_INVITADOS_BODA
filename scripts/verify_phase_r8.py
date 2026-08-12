"""PHASE R.8 — Product Acceptance & Freeze."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    print("\n> " + " ".join(map(str, cmd)))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


run([sys.executable, ROOT / "scripts/verify_phase_r7.py"])
run(["node", "--test", "DIRTEC_STUDIO_BUILD/builder/tests/*.mjs"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/build_builder.py"])
run([sys.executable, ROOT / "DIRTEC_STUDIO_BUILD/scripts/verify_builder_build.py"])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests_product_acceptance_r8",
    "invitaciones.tests_legacy_source_purge",
    "core.tests",
])
run([
    sys.executable,
    ROOT / "manage.py",
    "test",
    "invitaciones.tests.DashboardReportesTests.test_planner_solo_ve_eventos_asignados_de_su_empresa",
    "invitaciones.tests.DashboardReportesTests.test_dashboard_empresa_bloquea_catalogos_sin_permiso",
    "invitaciones.tests.DashboardReportesTests.test_dashboard_empresa_bloquea_usuarios_sin_permiso",
    "invitaciones.tests.DashboardReportesTests.test_usuario_empresa_no_ve_enlaces_admin_en_vistas_operativas",
    "invitaciones.tests.DashboardReportesTests.test_planner_no_asigna_proveedor_oculto_o_de_otra_empresa",
    "invitaciones.tests.DashboardReportesTests.test_planner_no_actualiza_servicio_de_evento_no_asignado",
    "invitaciones.tests.PortalTests.test_proveedor_no_puede_actualizar_servicio_ajeno",
    "invitaciones.tests.PortalTests.test_usuario_ajeno_no_puede_responder_aprobacion",
])
run([sys.executable, ROOT / "manage.py", "check"])
run([sys.executable, ROOT / "manage.py", "makemigrations", "--check"])
print("\nPHASE R.8 GATE OK")
