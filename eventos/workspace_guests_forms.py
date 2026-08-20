from django import forms

from invitaciones.models import Grupoinvitacion, Invitado


class WorkspaceGrupoForm(forms.ModelForm):
    integrantes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 5,
            "class": "app-textarea",
            "placeholder": "Una persona por línea para invitaciones familiares",
        }),
        help_text="Solo se usa al crear un grupo familiar.",
    )

    class Meta:
        model = Grupoinvitacion
        fields = [
            "nombre_grupo",
            "tipo",
            "telefono_contacto",
            "correo_contacto",
            "permitir_acompanantes_extra",
            "cantidad_extra_permitida",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "app-checkbox"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["telefono_contacto"].required = False
        self.fields["correo_contacto"].required = False
        self.fields["cantidad_extra_permitida"].required = False
        self.fields["cantidad_extra_permitida"].widget.attrs.setdefault("min", "0")

        if self.instance and self.instance.pk:
            # Changing PERSONAL <-> FAMILIAR after roster history exists is
            # deliberately not a casual edit.
            self.fields["tipo"].disabled = True
            self.fields["integrantes"].widget = forms.HiddenInput()

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get("tipo")
        extras_enabled = cleaned.get("permitir_acompanantes_extra")
        extras = int(cleaned.get("cantidad_extra_permitida") or 0)

        if not extras_enabled:
            cleaned["cantidad_extra_permitida"] = 0
        elif extras < 0:
            self.add_error("cantidad_extra_permitida", "No puede ser negativo.")

        if not self.instance.pk and tipo == "FAMILIAR":
            integrantes = [
                line.strip()
                for line in (cleaned.get("integrantes") or "").splitlines()
                if line.strip()
            ]
            if not integrantes:
                self.add_error("integrantes", "Agrega al menos una persona.")
            cleaned["integrantes_lista"] = integrantes
        else:
            cleaned["integrantes_lista"] = []

        return cleaned


class WorkspaceInvitadoForm(forms.ModelForm):
    class Meta:
        model = Invitado
        fields = [
            "nombre",
            "apellidos",
            "telefono",
            "correo",
            "tipo_persona",
            "menu_asignado",
            "mesa",
            "restricciones_alimentarias",
            "alergias",
            "notas",
        ]
        widgets = {
            "restricciones_alimentarias": forms.Textarea(attrs={"rows": 2}),
            "alergias": forms.Textarea(attrs={"rows": 2}),
            "notas": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for optional in (
            "apellidos", "telefono", "correo", "mesa",
            "restricciones_alimentarias", "alergias", "notas",
        ):
            self.fields[optional].required = False

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"


class WorkspaceRespuestaForm(forms.Form):
    respuesta = forms.ChoiceField(
        choices=[
            ("PENDIENTE", "Pendiente"),
            ("SI", "Sí asiste"),
            ("NO", "No asiste"),
        ],
        widget=forms.Select(attrs={"class": "app-select"}),
    )
