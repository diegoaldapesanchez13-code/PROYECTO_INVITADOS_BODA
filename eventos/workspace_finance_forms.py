from decimal import Decimal

from django import forms
from django.db.models import Q, Sum

from presupuesto.models import CategoriaGasto, GastoEvento, PagoClienteEvento, PagoEvento
from proveedores.models import Proveedor, ServicioEvento


class GastoEventoWorkspaceForm(forms.ModelForm):
    class Meta:
        model = GastoEvento
        fields = [
            "servicio_evento",
            "categoria",
            "proveedor",
            "concepto",
            "monto_estimado",
            "monto_real",
            "fecha_limite",
            "notas",
        ]
        widgets = {
            "servicio_evento": forms.Select(attrs={"class": "app-select"}),
            "categoria": forms.Select(attrs={"class": "app-select"}),
            "proveedor": forms.Select(attrs={"class": "app-select"}),
            "concepto": forms.TextInput(attrs={"class": "app-input", "maxlength": "160"}),
            "monto_estimado": forms.NumberInput(attrs={"class": "app-input", "min": "0", "step": "0.01"}),
            "monto_real": forms.NumberInput(attrs={"class": "app-input", "min": "0", "step": "0.01"}),
            "fecha_limite": forms.DateInput(attrs={"class": "app-input", "type": "date"}),
            "notas": forms.Textarea(attrs={"class": "app-textarea", "rows": "3"}),
        }

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        self.fields["categoria"].queryset = CategoriaGasto.objects.filter(activo=True).order_by("nombre")
        if evento is None:
            self.fields["servicio_evento"].queryset = ServicioEvento.objects.none()
            self.fields["proveedor"].queryset = Proveedor.objects.none()
        else:
            self.fields["servicio_evento"].queryset = (
                ServicioEvento.objects.filter(evento=evento)
                .exclude(estado_comercial="CANCELADO")
                .order_by("nombre_servicio", "id")
            )
            self.fields["proveedor"].queryset = (
                Proveedor.objects.filter(empresa=evento.empresa, activo=True)
                .order_by("nombre_comercial", "id")
            )
        self.fields["servicio_evento"].required = False
        self.fields["proveedor"].required = False
        self.fields["fecha_limite"].required = False
        self.fields["notas"].required = False

    def clean(self):
        cleaned = super().clean()
        estimado = cleaned.get("monto_estimado") or Decimal("0")
        real = cleaned.get("monto_real") or Decimal("0")

        if estimado < 0:
            self.add_error("monto_estimado", "El monto estimado no puede ser negativo.")
        if real < 0:
            self.add_error("monto_real", "El monto real no puede ser negativo.")
        if estimado <= 0 and real <= 0:
            raise forms.ValidationError("Captura un monto estimado o un monto real mayor a cero.")

        servicio = cleaned.get("servicio_evento")
        proveedor = cleaned.get("proveedor")
        if servicio and self.evento and servicio.evento_id != self.evento.id:
            self.add_error("servicio_evento", "El servicio no pertenece a este evento.")
        if proveedor and self.evento and proveedor.empresa_id != self.evento.empresa_id:
            self.add_error("proveedor", "El proveedor no pertenece a esta empresa.")
        if servicio and proveedor and servicio.proveedor_id and servicio.proveedor_id != proveedor.id:
            self.add_error("proveedor", "El proveedor no coincide con el proveedor del servicio.")

        if self.instance and self.instance.pk:
            total_pagado = (
                self.instance.pagos.filter(estado="ACTIVO")
                .aggregate(total=Sum("monto"))["total"]
                or Decimal("0")
            )
            objetivo = real if real > 0 else estimado
            if objetivo < total_pagado:
                raise forms.ValidationError(
                    "El monto objetivo no puede quedar por debajo de los pagos operativos activos."
                )
        return cleaned


class PagoOperativoWorkspaceForm(forms.ModelForm):
    class Meta:
        model = PagoEvento
        fields = [
            "monto",
            "fecha_pago",
            "metodo_pago",
            "referencia",
            "comprobante",
            "notas",
        ]
        widgets = {
            "monto": forms.NumberInput(attrs={"class": "app-input", "min": "0.01", "step": "0.01"}),
            "fecha_pago": forms.DateInput(attrs={"class": "app-input", "type": "date"}),
            "metodo_pago": forms.Select(attrs={"class": "app-select"}),
            "referencia": forms.TextInput(attrs={"class": "app-input", "maxlength": "120"}),
            "comprobante": forms.ClearableFileInput(attrs={"class": "app-input", "accept": ".pdf,.jpg,.jpeg,.png,.webp"}),
            "notas": forms.Textarea(attrs={"class": "app-textarea", "rows": "3"}),
        }

    def __init__(self, *args, gasto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.gasto = gasto
        self.fields["referencia"].required = False
        self.fields["comprobante"].required = False
        self.fields["notas"].required = False

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor a cero.")
        if self.gasto:
            saldo = Decimal(str(self.gasto.saldo_pendiente))
            if saldo <= 0:
                raise forms.ValidationError("Este gasto ya no tiene saldo pendiente.")
            if monto > saldo:
                raise forms.ValidationError(
                    f"El pago excede el saldo pendiente de {saldo:.2f}."
                )
        return monto


class MotivoGastoForm(forms.Form):
    motivo = forms.CharField(
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={"class": "app-textarea", "rows": "3"}),
    )


class MotivoPagoForm(forms.Form):
    motivo = forms.CharField(
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={"class": "app-textarea", "rows": "3"}),
    )


class RevisarPagoClienteWorkspaceForm(forms.Form):
    estado = forms.ChoiceField(
        choices=[
            ("RECIBIDO", "Marcar recibido"),
            ("OBSERVADO", "Marcar observado"),
        ],
        widget=forms.Select(attrs={"class": "app-select"}),
    )
    comentario_equipo = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"class": "app-textarea", "rows": "3"}),
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("estado") == "OBSERVADO" and not (cleaned.get("comentario_equipo") or "").strip():
            self.add_error(
                "comentario_equipo",
                "Agrega una observación para que quede claro qué debe revisarse.",
            )
        return cleaned
