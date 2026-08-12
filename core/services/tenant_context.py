"""Canonical tenant resolution for DIRTEC Event Studio."""

from dataclasses import dataclass

from django.core.exceptions import PermissionDenied
from django.http import Http404

from organizaciones.models import EmpresaSuscriptora, MembresiaEmpresa


@dataclass(frozen=True)
class TenantContext:
    empresa: EmpresaSuscriptora | None
    roles: frozenset[str]
    es_dirtec: bool
    puede_cambiar_empresa: bool
    origen: str

    @property
    def empresa_id(self):
        return self.empresa.id if self.empresa else None


def _company_ids_for_non_dirtec(user):
    from invitaciones.models import EventoBoda
    from proveedores.models import Proveedor

    ids = set(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            activo=True,
            empresa__activo=True,
        ).values_list("empresa_id", flat=True)
    )
    ids.update(
        EventoBoda.objects.filter(
            clientes=user,
            empresa__isnull=False,
            empresa__activo=True,
        ).values_list("empresa_id", flat=True)
    )
    ids.update(
        Proveedor.objects.filter(
            usuario=user,
            empresa__isnull=False,
            empresa__activo=True,
            activo=True,
        ).values_list("empresa_id", flat=True)
    )
    return ids


def _roles(user, empresa):
    if not empresa:
        return frozenset()
    return frozenset(
        MembresiaEmpresa.objects.filter(
            usuario=user,
            empresa=empresa,
            activo=True,
        ).values_list("rol", flat=True)
    )


def resolver_tenant_usuario(user, *, requested_company_id=None):
    from core.services.permisos import usuario_es_dirtec_operativo

    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Debes iniciar sesión.")

    if usuario_es_dirtec_operativo(user):
        empresa = None
        if requested_company_id:
            empresa = EmpresaSuscriptora.objects.filter(
                id=requested_company_id
            ).first()
            if not empresa:
                raise PermissionDenied("Empresa no válida.")
        return TenantContext(
            empresa=empresa,
            roles=frozenset({"DIRTEC"}),
            es_dirtec=True,
            puede_cambiar_empresa=True,
            origen="DIRTEC",
        )

    company_ids = _company_ids_for_non_dirtec(user)
    if not company_ids:
        return TenantContext(
            empresa=None,
            roles=frozenset(),
            es_dirtec=False,
            puede_cambiar_empresa=False,
            origen="SIN_TENANT",
        )

    if len(company_ids) > 1:
        raise PermissionDenied(
            "La cuenta está asociada a más de una empresa activa. "
            "DIRTEC debe corregir la asignación antes de continuar."
        )

    empresa = EmpresaSuscriptora.objects.filter(
        id=next(iter(company_ids)),
        activo=True,
    ).first()

    return TenantContext(
        empresa=empresa,
        roles=_roles(user, empresa),
        es_dirtec=False,
        puede_cambiar_empresa=False,
        origen="IDENTIDAD",
    )


def tenant_desde_request(request, *, allow_dirtec_switch=True):
    requested_company_id = None
    if allow_dirtec_switch:
        requested_company_id = (
            request.GET.get("empresa")
            or request.POST.get("empresa_id")
        )

    # requested_company_id only has effect for DIRTEC inside the resolver.
    return resolver_tenant_usuario(
        request.user,
        requested_company_id=requested_company_id,
    )


def exigir_tenant(
    request,
    *,
    roles=None,
    allow_dirtec_switch=True,
):
    context = tenant_desde_request(
        request,
        allow_dirtec_switch=allow_dirtec_switch,
    )
    if context.es_dirtec:
        return context
    if not context.empresa:
        raise PermissionDenied(
            "Tu cuenta no tiene una empresa activa."
        )
    if roles and not (
        context.roles & frozenset(roles)
    ):
        raise PermissionDenied(
            "Tu rol no tiene acceso a este espacio."
        )
    return context


def validar_slug_tenant(
    request,
    empresa_slug,
    *,
    roles=None,
):
    context = exigir_tenant(
        request,
        roles=roles,
        allow_dirtec_switch=False,
    )

    if context.es_dirtec:
        empresa = EmpresaSuscriptora.objects.filter(
            slug=empresa_slug
        ).first()
        if not empresa:
            raise Http404("Empresa no encontrada.")
        return TenantContext(
            empresa=empresa,
            roles=frozenset({"DIRTEC"}),
            es_dirtec=True,
            puede_cambiar_empresa=True,
            origen="DIRTEC_SLUG",
        )

    if (
        not context.empresa
        or context.empresa.slug != empresa_slug
    ):
        raise Http404(
            "Empresa no encontrada."
        )
    return context
