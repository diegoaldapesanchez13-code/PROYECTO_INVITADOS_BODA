from django import forms
from django.contrib.auth import get_user_model

from proveedores.models import ServicioEvento
from tareas.models import TareaEvento


class WorkspaceTareaForm(forms.ModelForm):
    class Meta:
        model = TareaEvento
        fields = [
            "titulo",
            "descripcion",
            "responsable",
            "servicio_evento",
            "prioridad",
            "categoria",
            "fecha_inicio",
            "fecha_limite",
            "hora_inicio",
            "hora_fin",
            "estado",
            "porcentaje_avance",
            "notas",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "notas": forms.Textarea(attrs={"rows": 3}),
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_limite": forms.DateInput(attrs={"type": "date"}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time"}),
            "hora_fin": forms.TimeInput(attrs={"type": "time"}),
            "porcentaje_avance": forms.NumberInput(attrs={"min": "0", "max": "100"}),
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

        self.fields["servicio_evento"].required = False
        self.fields["servicio_evento"].queryset = ServicioEvento.objects.filter(
            evento=evento,
            archivado_en__isnull=True,
        ).exclude(estado_operativo="CANCELADO").order_by("nombre_servicio")

        for optional in (
            "descripcion", "fecha_inicio", "fecha_limite", "hora_inicio",
            "hora_fin", "notas",
        ):
            self.fields[optional].required = False

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["titulo"].widget.attrs.setdefault("placeholder", "Ej. Confirmar montaje con proveedor")
        self.fields["porcentaje_avance"].required = False

        if self.instance and self.instance.pk and self.instance.archivado_en:
            for field in self.fields.values():
                field.disabled = True

    def clean(self):
        cleaned = super().clean()
        responsable = cleaned.get("responsable")
        servicio = cleaned.get("servicio_evento")
        inicio = cleaned.get("fecha_inicio")
        limite = cleaned.get("fecha_limite")
        hora_inicio = cleaned.get("hora_inicio")
        hora_fin = cleaned.get("hora_fin")
        estado = cleaned.get("estado")
        avance = cleaned.get("porcentaje_avance")

        if responsable and not responsable.membresias_empresa.filter(
            empresa=self.empresa,
            activo=True,
        ).exists():
            self.add_error("responsable", "El responsable debe pertenecer a la empresa.")

        if servicio and servicio.evento_id != self.evento.id:
            self.add_error("servicio_evento", "El servicio debe pertenecer al mismo evento.")

        if inicio and limite and limite < inicio:
            self.add_error("fecha_limite", "La fecha límite no puede ser anterior al inicio.")

        if inicio and limite and inicio == limite and hora_inicio and hora_fin and hora_fin <= hora_inicio:
            self.add_error("hora_fin", "La hora final debe ser posterior a la hora inicial.")

        if avance is None:
            cleaned["porcentaje_avance"] = 0

        if estado == "COMPLETADA":
            cleaned["porcentaje_avance"] = 100

        return cleaned
