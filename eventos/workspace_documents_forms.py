from django import forms

from documentos.models import DocumentoEvento
from proveedores.models import Proveedor, ServicioEvento


class DocumentoWorkspaceForm(forms.ModelForm):
    class Meta:
        model = DocumentoEvento
        fields = [
            "tipo_documento",
            "titulo",
            "archivo",
            "servicio_evento",
            "proveedor",
            "descripcion",
            "visible_cliente",
            "visible_proveedor",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, evento=None, empresa=None, **kwargs):
        self.evento = evento
        self.empresa = empresa or getattr(evento, "empresa", None)
        super().__init__(*args, **kwargs)

        self.fields["servicio_evento"].required = False
        self.fields["proveedor"].required = False
        self.fields["descripcion"].required = False

        if evento is not None:
            self.fields["servicio_evento"].queryset = (
                ServicioEvento.objects.filter(evento=evento)
                .select_related("proveedor")
                .order_by("categoria", "id")
            )
        else:
            self.fields["servicio_evento"].queryset = ServicioEvento.objects.none()

        if self.empresa is not None:
            self.fields["proveedor"].queryset = (
                Proveedor.objects.filter(empresa=self.empresa, activo=True)
                .order_by("nombre_comercial")
            )
        else:
            self.fields["proveedor"].queryset = Proveedor.objects.none()

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "app-checkbox"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs["class"] = "app-file"
                field.widget.attrs["accept"] = ".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.webp"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["archivo"].help_text = (
            "PDF, Word, Excel, TXT o imagen. Máximo 25 MB."
        )

    def clean(self):
        cleaned = super().clean()
        servicio = cleaned.get("servicio_evento")
        proveedor = cleaned.get("proveedor")

        if servicio and self.evento and servicio.evento_id != self.evento.id:
            self.add_error(
                "servicio_evento",
                "El servicio debe pertenecer a este evento.",
            )

        if proveedor and self.empresa and proveedor.empresa_id != self.empresa.id:
            self.add_error(
                "proveedor",
                "El proveedor debe pertenecer a esta empresa.",
            )

        if servicio and servicio.proveedor_id:
            if proveedor and proveedor.id != servicio.proveedor_id:
                self.add_error(
                    "proveedor",
                    "El proveedor debe coincidir con el proveedor del servicio seleccionado.",
                )
            elif not proveedor:
                cleaned["proveedor"] = servicio.proveedor

        return cleaned


class DocumentoArchivoForm(forms.Form):
    motivo = forms.CharField(
        required=False,
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": "app-textarea",
                "rows": 2,
                "placeholder": "Motivo opcional para conservar contexto",
            }
        ),
    )



class DocumentoReemplazoForm(forms.Form):
    archivo = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "app-file",
                "accept": ".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.webp",
            }
        ),
        help_text="PDF, Word, Excel, TXT o imagen. Máximo 25 MB.",
    )


class DocumentoEliminarForm(forms.Form):
    confirmacion = forms.CharField(
        max_length=20,
        widget=forms.TextInput(
            attrs={
                "class": "app-input",
                "placeholder": "Escribe ELIMINAR",
                "autocomplete": "off",
            }
        ),
    )

    def clean_confirmacion(self):
        value = (self.cleaned_data.get("confirmacion") or "").strip().upper()
        if value != "ELIMINAR":
            raise forms.ValidationError("Escribe ELIMINAR para confirmar.")
        return value
