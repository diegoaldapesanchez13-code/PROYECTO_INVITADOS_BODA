from django import forms
from django.contrib.auth import get_user_model

from itinerario.models import ActividadItinerario
from proveedores.models import Proveedor, ServicioEvento


class WorkspaceActividadForm(forms.ModelForm):
    class Meta:
        model = ActividadItinerario
        fields = [
            "tipo",
            "titulo",
            "descripcion",
            "categoria",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "ubicacion",
            "responsable",
            "proveedor",
            "servicio_evento",
            "prioridad",
            "estado",
            "orden",
            "notas",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "notas": forms.Textarea(attrs={"rows": 3}),
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
            "orden": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, empresa, evento, **kwargs):
        self.empresa = empresa
        self.evento = evento
        super().__init__(*args, **kwargs)

        User = get_user_model()
        self.fields["responsable"].required = False
        self.fields["responsable"].queryset = User.objects.filter(
            membresias_empresa__empresa=empresa,
            membresias_empresa__activo=True,
            membresias_empresa__rol__in={"ADMIN_EMPRESA", "WEDDING_PLANNER", "VENTAS"},
            is_active=True,
        ).distinct().order_by("first_name", "last_name", "username")

        self.fields["proveedor"].required = False
        self.fields["proveedor"].queryset = Proveedor.objects.filter(
            empresa=empresa,
            activo=True,
        ).order_by("nombre_comercial")

        self.fields["servicio_evento"].required = False
        self.fields["servicio_evento"].queryset = ServicioEvento.objects.filter(
            evento=evento,
            archivado_en__isnull=True,
        ).exclude(estado_operativo="CANCELADO").order_by("nombre_servicio")

        for optional in ("descripcion", "hora_fin", "ubicacion", "notas"):
            self.fields[optional].required = False
        self.fields["orden"].required = False

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["titulo"].widget.attrs.setdefault("placeholder", "Ej. Visita técnica a la sede")

        if self.instance and self.instance.pk and self.instance.archivado_en:
            for field in self.fields.values():
                field.disabled = True

    def clean(self):
        cleaned = super().clean()
        responsable = cleaned.get("responsable")
        proveedor = cleaned.get("proveedor")
        servicio = cleaned.get("servicio_evento")

        if responsable and not responsable.membresias_empresa.filter(
            empresa=self.empresa,
            activo=True,
        ).exists():
            self.add_error("responsable", "El responsable debe pertenecer a la empresa.")

        if proveedor and proveedor.empresa_id != self.empresa.id:
            self.add_error("proveedor", "El proveedor debe pertenecer a la empresa.")

        if servicio and servicio.evento_id != self.evento.id:
            self.add_error("servicio_evento", "El servicio debe pertenecer al mismo evento.")

        if cleaned.get("orden") is None:
            cleaned["orden"] = 0

        return cleaned
