from pathlib import Path

from django.test import SimpleTestCase
from django.template.loader import get_template


class WorkspaceRuntimeNavigationTests(SimpleTestCase):
    def test_workspace_base_loads_runtime(self):
        template = get_template("eventos/workspace/base.html")
        content = Path(template.origin.name).read_text(encoding="utf-8")
        self.assertIn("workspace_runtime.css", content)
        self.assertIn("workspace_runtime.js", content)
        self.assertIn("data-workspace-shell", content)

    def test_workspace_tabs_are_enhanced_but_exit_is_native(self):
        template = get_template("eventos/workspace/base.html")
        content = Path(template.origin.name).read_text(encoding="utf-8")
        self.assertIn("data-workspace-module-link", content)
        self.assertIn("data-workspace-native", content)

    def test_runtime_uses_history_and_scroll_restoration(self):
        root = Path(__file__).resolve().parent
        runtime = (
            root / "static" / "eventos" / "js" / "workspace_runtime.js"
        ).read_text(encoding="utf-8")
        self.assertIn("history.pushState", runtime)
        self.assertIn("history.scrollRestoration", runtime)
        self.assertIn("window.scrollTo", runtime)
        self.assertIn("dirtec:workspace:loaded", runtime)

    def test_kanban_reinitializes_after_partial_navigation(self):
        root = Path(__file__).resolve().parent
        task_js = (
            root / "static" / "eventos" / "js" / "workspace_tasks_r4.js"
        ).read_text(encoding="utf-8")
        self.assertIn("dirtec:workspace:loaded", task_js)
        self.assertIn("form.requestSubmit()", task_js)
