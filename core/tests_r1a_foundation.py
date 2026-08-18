from django.contrib.auth import get_user_model
from django.template.loader import get_template
from django.test import RequestFactory, SimpleTestCase, TestCase

from core.services.branding import get_brand_context
from organizaciones.models import EmpresaSuscriptora


class BrandContextTests(TestCase):
    def test_default_brand_context_is_stable(self):
        brand = get_brand_context()
        self.assertEqual(brand["product_name"], "DIRTEC Event Studio")
        self.assertEqual(brand["primary"], "#1F2937")
        self.assertEqual(brand["secondary"], "#64748B")
        self.assertEqual(brand["accent"], "#2563EB")

    def test_company_brand_uses_existing_fields(self):
        empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Casa Demo",
            slug="casa-demo-r1a",
            colores_marca={
                "principal": "#56644a",
                "secundario": "#d5cbb8",
                "acento": "#123ABC",
            },
        )
        brand = get_brand_context(empresa)
        self.assertEqual(brand["company_name"], "Casa Demo")
        self.assertEqual(brand["primary"], "#56644A")
        self.assertEqual(brand["secondary"], "#D5CBB8")
        self.assertEqual(brand["accent"], "#123ABC")

    def test_invalid_colors_fall_back_safely(self):
        empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa",
            slug="empresa-invalid-brand-r1a",
            colores_marca={
                "primary": "red",
                "secondary": "#123",
                "accent": "var(--x)",
            },
        )
        brand = get_brand_context(empresa)
        self.assertEqual(brand["primary"], "#1F2937")
        self.assertEqual(brand["secondary"], "#64748B")
        self.assertEqual(brand["accent"], "#2563EB")


class AppFoundationTemplateTests(SimpleTestCase):
    def test_foundation_templates_compile(self):
        templates = [
            "core/app/base.html",
            "core/app/components/topbar.html",
            "core/app/components/sidebar.html",
            "core/app/components/mobile_nav.html",
            "core/app/components/toast_region.html",
            "core/app/components/modal_root.html",
            "core/app/components/empty_state.html",
        ]
        for template_name in templates:
            with self.subTest(template=template_name):
                self.assertIsNotNone(get_template(template_name))

    def test_base_renders_with_minimal_context(self):
        User = get_user_model()
        request = RequestFactory().get("/")
        request.user = User(username="demo")
        html = get_template("core/app/base.html").render(
            {
                "request": request,
                "brand_context": get_brand_context(),
                "navigation": {"items": [], "mobile_items": []},
                "app_context": {"page_title": "Preview"},
            }
        )
        self.assertIn("DIRTEC Event Studio", html)
        self.assertIn("core/app/tokens.css", html)
        self.assertIn("core/app/app.js", html)
        self.assertIn('id="main-content"', html)

    def test_mobile_navigation_has_accessible_label(self):
        html = get_template("core/app/components/mobile_nav.html").render(
            {"navigation": {"mobile_items": []}}
        )
        self.assertIn('aria-label="Navegación móvil"', html)
