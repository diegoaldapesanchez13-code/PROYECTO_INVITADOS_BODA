import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from documentos.models import DocumentoEvento
from invitaciones.models import EventoBoda
from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa
from proveedores.models import Proveedor


TEST_MEDIA_ROOT = tempfile.mkdtemp(prefix="dirtec-r4ga-docs-")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentsWorkspaceR4GATests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        User = get_user_model()

        self.empresa = EmpresaSuscriptora.objects.create(
            nombre_comercial="Empresa R4GA",
            slug="empresa-r4ga",
        )
        self.otra = EmpresaSuscriptora.objects.create(
            nombre_comercial="Otra R4GA",
            slug="otra-r4ga",
        )

        self.admin = User.objects.create_user(
            username="admin-r4ga",
            password="Pass-R4GA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin,
            rol="ADMIN_EMPRESA",
        )

        self.planner = User.objects.create_user(
            username="planner-r4ga",
            password="Pass-R4GA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.planner,
            rol="WEDDING_PLANNER",
        )

        self.evento = EventoBoda.objects.create(
            empresa=self.empresa,
            nombre_evento="Evento R4GA",
            wedding_planner=self.planner,
        )

    def url(self):
        return reverse(
            "k9_evento_documentos",
            kwargs={
                "empresa_slug": self.empresa.slug,
                "evento_id": self.evento.id,
            },
        )

    def upload(self, *, title="Contrato principal", doc_type="CONTRATO"):
        return self.client.post(
            self.url(),
            {
                "tipo_documento": doc_type,
                "titulo": title,
                "archivo": SimpleUploadedFile(
                    "contrato.txt",
                    b"contenido seguro de prueba",
                    content_type="text/plain",
                ),
                "descripcion": "Documento R4G-A",
            },
        )

    def make_document(self, **kwargs):
        defaults = {
            "evento": self.evento,
            "tipo_documento": "CONTRATO",
            "titulo": "Documento existente",
            "archivo": SimpleUploadedFile(
                "existente.txt",
                b"archivo existente",
                content_type="text/plain",
            ),
            "cargado_por": self.admin,
        }
        defaults.update(kwargs)
        return DocumentoEvento.objects.create(**defaults)

    def test_documents_tab_is_enabled(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "k9_evento_resumen",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                },
            )
        )
        tab = next(
            item
            for item in response.context["workspace_navigation"]["tabs"]
            if item["key"] == "documentos"
        )
        self.assertTrue(tab["enabled"])
        self.assertEqual(tab["url"], self.url())

    def test_documents_page_uses_premium_workspace(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Documentos")
        self.assertContains(response, "workspace_documents_r4.css")
        self.assertContains(response, "Subir documento")

    def test_admin_can_upload_document(self):
        self.client.force_login(self.admin)
        response = self.upload()
        self.assertEqual(response.status_code, 302)

        document = DocumentoEvento.objects.get(evento=self.evento)
        self.assertEqual(document.titulo, "Contrato principal")
        self.assertEqual(document.tipo_documento, "CONTRATO")
        self.assertEqual(document.cargado_por, self.admin)
        self.assertIsNone(document.archivado_en)

    def test_assigned_planner_can_upload_document(self):
        self.client.force_login(self.planner)
        response = self.upload(title="Archivo planner", doc_type="LISTA")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            DocumentoEvento.objects.filter(
                evento=self.evento,
                titulo="Archivo planner",
            ).exists()
        )

    def test_invalid_file_extension_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url(),
            {
                "tipo_documento": "OTRO",
                "titulo": "Archivo inválido",
                "archivo": SimpleUploadedFile(
                    "script.exe",
                    b"not executable",
                    content_type="application/octet-stream",
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            DocumentoEvento.objects.filter(
                evento=self.evento,
                titulo="Archivo inválido",
            ).exists()
        )

    def test_secure_download_uses_existing_secure_route(self):
        document = self.make_document()
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "secure_documento_evento",
                kwargs={"documento_id": document.id},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_archive_preserves_document(self):
        document = self.make_document()
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "k9_documento_archivar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": document.id,
                },
            ),
            {"motivo": "Versión anterior"},
        )
        self.assertEqual(response.status_code, 302)

        document.refresh_from_db()
        self.assertIsNotNone(document.archivado_en)
        self.assertEqual(document.archivado_por, self.admin)
        self.assertEqual(document.motivo_archivo, "Versión anterior")
        self.assertTrue(DocumentoEvento.objects.filter(pk=document.id).exists())

    def test_restore_document(self):
        document = self.make_document()
        self.client.force_login(self.admin)

        self.client.post(
            reverse(
                "k9_documento_archivar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": document.id,
                },
            ),
            {"motivo": "Temporal"},
        )
        response = self.client.post(
            reverse(
                "k9_documento_restaurar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": document.id,
                },
            )
        )
        self.assertEqual(response.status_code, 302)

        document.refresh_from_db()
        self.assertIsNone(document.archivado_en)
        self.assertIsNone(document.archivado_por)
        self.assertIsNone(document.motivo_archivo)

    def test_filters_active_and_archived(self):
        active = self.make_document(titulo="Documento Alfa R4GA")
        archived = self.make_document(titulo="Documento Beta R4GA")
        self.client.force_login(self.admin)
        self.client.post(
            reverse(
                "k9_documento_archivar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": archived.id,
                },
            )
        )

        response = self.client.get(self.url(), {"estado": "ACTIVOS"})
        self.assertEqual(response.status_code, 200)
        active_ids = {documento.id for documento in response.context["documentos"]}
        self.assertIn(active.id, active_ids)
        self.assertNotIn(archived.id, active_ids)

        response = self.client.get(self.url(), {"estado": "ARCHIVADOS"})
        self.assertEqual(response.status_code, 200)
        archived_ids = {documento.id for documento in response.context["documentos"]}
        self.assertIn(archived.id, archived_ids)
        self.assertNotIn(active.id, archived_ids)

    def test_provider_from_other_tenant_is_rejected(self):
        provider = Proveedor.objects.create(
            empresa=self.otra,
            nombre_comercial="Proveedor externo",
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url(),
            {
                "tipo_documento": "COTIZACION",
                "titulo": "Cruce tenant",
                "archivo": SimpleUploadedFile(
                    "cruce.txt",
                    b"cruce",
                    content_type="text/plain",
                ),
                "proveedor": provider.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            DocumentoEvento.objects.filter(
                evento=self.evento,
                titulo="Cruce tenant",
            ).exists()
        )

    def test_other_company_cannot_open_workspace(self):
        outsider = get_user_model().objects.create_user(
            username="outsider-r4ga",
            password="Pass-R4GA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.otra,
            usuario=outsider,
            rol="ADMIN_EMPRESA",
        )
        self.client.force_login(outsider)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 404)

    def test_unassigned_planner_cannot_open_documents(self):
        other = get_user_model().objects.create_user(
            username="other-planner-r4ga",
            password="Pass-R4GA-2026!",
        )
        MembresiaEmpresa.objects.create(
            empresa=self.empresa,
            usuario=other,
            rol="WEDDING_PLANNER",
        )
        self.client.force_login(other)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 403)


    def test_replace_file_preserves_document_metadata_and_deletes_old_file(self):
        document = self.make_document(
            titulo="Contrato reemplazable",
            visible_cliente=True,
        )
        old_name = document.archivo.name
        old_storage = document.archivo.storage
        self.assertTrue(old_storage.exists(old_name))

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "k9_documento_reemplazar",
                    kwargs={
                        "empresa_slug": self.empresa.slug,
                        "evento_id": self.evento.id,
                        "documento_id": document.id,
                    },
                ),
                {
                    "archivo": SimpleUploadedFile(
                        "nueva-version.txt",
                        b"contenido nuevo",
                        content_type="text/plain",
                    )
                },
            )

        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.titulo, "Contrato reemplazable")
        self.assertTrue(document.visible_cliente)
        self.assertNotEqual(document.archivo.name, old_name)
        self.assertTrue(document.archivo.storage.exists(document.archivo.name))
        self.assertFalse(old_storage.exists(old_name))

    def test_replace_rejects_invalid_file_and_keeps_original(self):
        document = self.make_document(titulo="No reemplazar con exe")
        old_name = document.archivo.name

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_documento_reemplazar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": document.id,
                },
            ),
            {
                "archivo": SimpleUploadedFile(
                    "malware.exe",
                    b"contenido",
                    content_type="application/octet-stream",
                )
            },
        )
        self.assertEqual(response.status_code, 302)
        document.refresh_from_db()
        self.assertEqual(document.archivo.name, old_name)
        self.assertTrue(document.archivo.storage.exists(old_name))

    def test_delete_requires_explicit_confirmation(self):
        document = self.make_document(titulo="Documento protegido")

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse(
                "k9_documento_eliminar",
                kwargs={
                    "empresa_slug": self.empresa.slug,
                    "evento_id": self.evento.id,
                    "documento_id": document.id,
                },
            ),
            {"confirmacion": "NO"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DocumentoEvento.objects.filter(pk=document.id).exists())

    def test_delete_removes_database_record_and_physical_file(self):
        document = self.make_document(titulo="Documento para eliminar")
        file_name = document.archivo.name
        storage = document.archivo.storage
        self.assertTrue(storage.exists(file_name))

        self.client.force_login(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "k9_documento_eliminar",
                    kwargs={
                        "empresa_slug": self.empresa.slug,
                        "evento_id": self.evento.id,
                        "documento_id": document.id,
                    },
                ),
                {"confirmacion": "ELIMINAR"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(DocumentoEvento.objects.filter(pk=document.id).exists())
        self.assertFalse(storage.exists(file_name))
