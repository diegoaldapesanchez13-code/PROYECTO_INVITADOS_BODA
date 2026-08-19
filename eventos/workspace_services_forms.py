from django import forms
from django.db.models import Q

from catalogo.models import ProveedorServicioCatalogo, ServicioCatalogo
from proveedores.models import Proveedor, ServicioEvento


class WorkspaceServicioForm(forms.ModelForm):
    class Meta:
        model = ServicioEvento
        fields = [
            "servicio_catalogo_k9",
            "nombre_servicio",
            "descripcion",
            "prestacion_tipo",
            "proveedor",
            "fecha_servicio",
            "hora_inicio",
            "hora_fin",
            "lugar",
            "estado_operativo",
            "costo_proveedor",
            "notas_internas",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "notas_internas": forms.Textarea(attrs={"rows": 3}),
            "fecha_servicio": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, empresa, can_finance=False, **kwargs):
        self.empresa = empresa
        self.can_finance = can_finance
        super().__init__(*args, **kwargs)

        self.fields["servicio_catalogo_k9"].required = False
        self.fields["nombre_servicio"].required = False
        self.fields["proveedor"].required = False

        # Estos campos tienen defaults de dominio y no deben bloquear el
        # formulario cuando el POST mínimo no los envía explícitamente.
        self.fields["descripcion"].required = False
        self.fields["fecha_servicio"].required = False
        self.fields["hora_inicio"].required = False
        self.fields["hora_fin"].required = False
        self.fields["lugar"].required = False
        self.fields["notas_internas"].required = False
        if "costo_proveedor" in self.fields:
            self.fields["costo_proveedor"].required = False

        self.fields["servicio_catalogo_k9"].queryset = ServicioCatalogo.objects.filter(
            empresa=empresa,
            activo=True,
        ).order_by("categoria", "nombre")

        current_provider_id = self.instance.proveedor_id if self.instance and self.instance.pk else None
        catalog_id = None
        if self.is_bound:
            raw = self.data.get(self.add_prefix("servicio_catalogo_k9"))
            try:
                catalog_id = int(raw) if raw else None
            except (TypeError, ValueError):
                catalog_id = None
        elif self.instance and self.instance.pk:
            catalog_id = self.instance.servicio_catalogo_k9_id

        provider_qs = Proveedor.objects.filter(
            empresa=empresa,
            activo=True,
        )

        if catalog_id:
            compatible_ids = ProveedorServicioCatalogo.objects.filter(
                servicio_catalogo_id=catalog_id,
                servicio_catalogo__empresa=empresa,
                servicio_catalogo__activo=True,
                proveedor__empresa=empresa,
                proveedor__activo=True,
                activo=True,
            ).values_list("proveedor_id", flat=True)

            provider_filter = Q(id__in=compatible_ids)
            if current_provider_id:
                provider_filter |= Q(id=current_provider_id)
            provider_qs = provider_qs.filter(provider_filter)

        self.fields["proveedor"].queryset = provider_qs.order_by("nombre_comercial")

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["nombre_servicio"].widget.attrs.setdefault(
            "placeholder",
            "Ej. Fotografía, valet parking, planta de luz",
        )
        self.fields["costo_proveedor"].widget.attrs.setdefault("min", "0")

        if not can_finance:
            self.fields.pop("costo_proveedor")
        else:
            # El costo puede quedar por definir. Persistimos 0.00 como valor
            # neutral del modelo cuando el usuario no captura nada.
            self.fields["costo_proveedor"].required = False

        # Contract-derived identity is frozen. Operational assignment remains editable.
        if self.instance and self.instance.pk and self.instance.contrato_origen_id:
            self.fields["servicio_catalogo_k9"].disabled = True
            self.fields["nombre_servicio"].disabled = True
            self.fields["descripcion"].disabled = True

    def clean(self):
        cleaned = super().clean()
        catalog = cleaned.get("servicio_catalogo_k9")
        nombre = (cleaned.get("nombre_servicio") or "").strip()
        prestacion = cleaned.get("prestacion_tipo")
        proveedor = cleaned.get("proveedor")

        if not catalog and not nombre:
            self.add_error(
                "nombre_servicio",
                "Selecciona un servicio de catálogo o escribe un nombre.",
            )

        if catalog and not nombre:
            cleaned["nombre_servicio"] = catalog.nombre

        if prestacion in {"POR_DEFINIR", "EMPRESA"}:
            cleaned["proveedor"] = None
            proveedor = None

        if proveedor and prestacion != "PROVEEDOR":
            cleaned["prestacion_tipo"] = "PROVEEDOR"
            prestacion = "PROVEEDOR"

        if prestacion == "PROVEEDOR" and catalog and proveedor:
            # Historical/current assignment remains valid even if capability was
            # later deactivated, but a NEW provider assignment must be compatible.
            provider_changed = (
                not self.instance
                or not self.instance.pk
                or self.instance.proveedor_id != proveedor.id
                or self.instance.servicio_catalogo_k9_id != catalog.id
            )
            if provider_changed and not ProveedorServicioCatalogo.objects.filter(
                proveedor=proveedor,
                servicio_catalogo=catalog,
                activo=True,
                proveedor__activo=True,
                servicio_catalogo__activo=True,
                proveedor__empresa=self.empresa,
                servicio_catalogo__empresa=self.empresa,
            ).exists():
                self.add_error(
                    "proveedor",
                    "Este proveedor no está habilitado para ofrecer el servicio seleccionado.",
                )

        inicio = cleaned.get("hora_inicio")
        fin = cleaned.get("hora_fin")
        if inicio and fin and fin <= inicio:
            self.add_error("hora_fin", "La hora final debe ser posterior al inicio.")

        return cleaned
