from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.services.authorization import Actions, usuario_puede_evento
from documentos.models import DocumentoEvento

from .workspace_documents import (
    archivar_documento,
    crear_documento,
    eliminar_documento,
    reemplazar_archivo_documento,
    restaurar_documento,
)
from .workspace_documents_forms import (
    DocumentoArchivoForm,
    DocumentoEliminarForm,
    DocumentoReemplazoForm,
    DocumentoWorkspaceForm,
)
from .workspace_views import (
    _app_context,
    _contexto_empresa,
    _evento_visible,
    _return_context,
    _url_with_return,
    _workspace_context,
)


def _redirect_documentos(empresa, evento, return_to, *, estado="ACTIVOS"):
    url = reverse(
        "k9_evento_documentos",
        kwargs={
            "empresa_slug": empresa.slug,
            "evento_id": evento.id,
        },
    )
    if estado:
        url = f"{url}?estado={estado}"
    return _url_with_return(url, return_to)


def _documento_evento(evento, documento_id):
    return get_object_or_404(
        DocumentoEvento.objects.select_related(
            "evento",
            "evento__empresa",
            "servicio_evento",
            "servicio_evento__proveedor",
            "proveedor",
            "cargado_por",
            "archivado_por",
        ),
        pk=documento_id,
        evento=evento,
    )


@login_required(login_url="/login/")
def evento_documentos(request, empresa_slug, evento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_OPERATIONS,
    )
    return_to = _return_context(request, empresa)

    puede_gestionar = usuario_puede_evento(
        request.user,
        evento,
        Actions.EVENT_OPERATIONS,
    )
    if not puede_gestionar:
        raise PermissionDenied("No tienes permiso para consultar documentos del evento.")

    estado = (request.GET.get("estado") or "ACTIVOS").strip().upper()
    tipo = (request.GET.get("tipo") or "").strip().upper()
    q = (request.GET.get("q") or "").strip()

    qs = (
        DocumentoEvento.objects.filter(evento=evento)
        .select_related(
            "servicio_evento",
            "servicio_evento__proveedor",
            "proveedor",
            "cargado_por",
            "archivado_por",
        )
        .order_by("-fecha_carga", "-id")
    )

    if estado == "ARCHIVADOS":
        qs = qs.filter(archivado_en__isnull=False)
    else:
        estado = "ACTIVOS"
        qs = qs.filter(archivado_en__isnull=True)

    valid_types = {key for key, _label in DocumentoEvento.TIPOS}
    if tipo in valid_types:
        qs = qs.filter(tipo_documento=tipo)
    else:
        tipo = ""

    if q:
        qs = qs.filter(
            Q(titulo__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(proveedor__nombre_comercial__icontains=q)
            | Q(servicio_evento__categoria__icontains=q)
        )

    form = DocumentoWorkspaceForm(
        request.POST or None,
        request.FILES or None,
        evento=evento,
        empresa=empresa,
    )

    if request.method == "POST":
        if not form.is_valid():
            messages.error(request, "Revisa los datos del documento.")
        else:
            try:
                documento = crear_documento(
                    evento=evento,
                    cleaned_data=dict(form.cleaned_data),
                    user=request.user,
                    request=request,
                )
            except ValidationError as exc:
                for error in exc.messages:
                    messages.error(request, error)
            else:
                messages.success(request, f"Documento cargado: {documento.titulo}.")
                return redirect(
                    _redirect_documentos(
                        empresa,
                        evento,
                        return_to,
                        estado="ACTIVOS",
                    )
                )

    activos_total = DocumentoEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
    ).count()
    archivados_total = DocumentoEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=False,
    ).count()
    cliente_total = DocumentoEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
        visible_cliente=True,
    ).count()
    proveedor_total = DocumentoEvento.objects.filter(
        evento=evento,
        archivado_en__isnull=True,
        visible_proveedor=True,
    ).count()

    context = _app_context(
        request,
        empresa,
        title=evento.titulo_evento,
        section="Event Workspace",
    )
    context.update(
        {
            "evento": evento,
            "workspace_active": "documentos",
            "workspace_navigation": _workspace_context(
                request,
                empresa=empresa,
                evento=evento,
                active_key="documentos",
            ),
            "return_to": return_to,
            "puede_editar": puede_gestionar,
            "puede_gestionar": puede_gestionar,
            "documentos": list(qs),
            "documento_form": form,
            "archivo_form": DocumentoArchivoForm(),
            "reemplazo_form": DocumentoReemplazoForm(),
            "eliminar_form": DocumentoEliminarForm(),
            "estado_filtro": estado,
            "tipo_filtro": tipo,
            "busqueda": q,
            "tipos_documento": DocumentoEvento.TIPOS,
            "activos_total": activos_total,
            "archivados_total": archivados_total,
            "cliente_total": cliente_total,
            "proveedor_total": proveedor_total,
        }
    )
    return render(
        request,
        "eventos/workspace/documentos.html",
        context,
    )


@login_required(login_url="/login/")
@require_POST
def documento_archivar(request, empresa_slug, evento_id, documento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_OPERATIONS,
    )
    return_to = _return_context(request, empresa)

    documento = _documento_evento(evento, documento_id)
    form = DocumentoArchivoForm(request.POST)

    if not form.is_valid():
        messages.error(request, "No se pudo archivar el documento.")
    else:
        archivar_documento(
            documento,
            motivo=form.cleaned_data.get("motivo") or "",
            user=request.user,
            request=request,
        )
        messages.success(request, f"Documento archivado: {documento.titulo}.")

    return redirect(
        _redirect_documentos(
            empresa,
            evento,
            return_to,
            estado="ACTIVOS",
        )
    )


@login_required(login_url="/login/")
@require_POST
def documento_restaurar(request, empresa_slug, evento_id, documento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_OPERATIONS,
    )
    return_to = _return_context(request, empresa)

    documento = _documento_evento(evento, documento_id)
    restaurar_documento(
        documento,
        user=request.user,
        request=request,
    )
    messages.success(request, f"Documento restaurado: {documento.titulo}.")

    return redirect(
        _redirect_documentos(
            empresa,
            evento,
            return_to,
            estado="ARCHIVADOS",
        )
    )



@login_required(login_url="/login/")
@require_POST
def documento_reemplazar(request, empresa_slug, evento_id, documento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_OPERATIONS,
    )
    return_to = _return_context(request, empresa)

    documento = _documento_evento(evento, documento_id)
    form = DocumentoReemplazoForm(request.POST, request.FILES)

    if not form.is_valid():
        messages.error(request, "Selecciona un archivo válido para reemplazar.")
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, str(error))
    else:
        try:
            reemplazar_archivo_documento(
                documento,
                nuevo_archivo=form.cleaned_data["archivo"],
                user=request.user,
                request=request,
            )
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)
        else:
            messages.success(
                request,
                f"Archivo reemplazado: {documento.titulo}.",
            )

    return redirect(
        _redirect_documentos(
            empresa,
            evento,
            return_to,
            estado="ARCHIVADOS" if documento.archivado_en else "ACTIVOS",
        )
    )


@login_required(login_url="/login/")
@require_POST
def documento_eliminar(request, empresa_slug, evento_id, documento_id):
    tenant, _roles = _contexto_empresa(request, empresa_slug)
    empresa = tenant.empresa
    evento = _evento_visible(
        request.user,
        empresa,
        evento_id,
        action=Actions.EVENT_OPERATIONS,
    )
    return_to = _return_context(request, empresa)

    documento = _documento_evento(evento, documento_id)
    estado = "ARCHIVADOS" if documento.archivado_en else "ACTIVOS"
    form = DocumentoEliminarForm(request.POST)

    if not form.is_valid():
        messages.error(
            request,
            "No se eliminó el documento. Escribe ELIMINAR para confirmar.",
        )
    else:
        titulo = documento.titulo
        eliminar_documento(
            documento,
            user=request.user,
            request=request,
        )
        messages.success(
            request,
            f"Documento eliminado permanentemente: {titulo}.",
        )

    return redirect(
        _redirect_documentos(
            empresa,
            evento,
            return_to,
            estado=estado,
        )
    )
