from django import forms

from paquetes.forms import PropuestaEventoForm, PropuestaLineaForm


class WorkspacePropuestaForm(PropuestaEventoForm):
    """
    Proposal form adapted to the Event Workspace.

    CONTRATADO is never a user-selectable state. A proposal reaches that state
    only after the contract-generation service succeeds.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_states = {
            "BORRADOR",
            "PROPUESTA",
            "EN_REVISION",
            "ACEPTADO",
            "CANCELADO",
        }
        self.fields["estado"].choices = [
            choice
            for choice in self.fields["estado"].choices
            if choice[0] in allowed_states
        ]

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["adultos"].widget.attrs.setdefault("min", "0")
        self.fields["ninos"].widget.attrs.setdefault("min", "0")
        self.fields["descuento"].widget.attrs.setdefault("min", "0")

        if self.instance and self.instance.pk and self.instance.estado == "CONTRATADO":
            for field in self.fields.values():
                field.disabled = True


class WorkspaceLineaForm(PropuestaLineaForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "app-select"
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = "app-textarea"
            else:
                field.widget.attrs["class"] = "app-input"

        self.fields["tarifa"].widget.attrs.setdefault("min", "0")
        self.fields["cantidad"].widget.attrs.setdefault("min", "0.01")
