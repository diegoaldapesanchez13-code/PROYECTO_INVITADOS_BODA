from django import forms
from django.contrib.auth import get_user_model

from invitaciones.models import EventoBoda
from organizaciones.models import MembresiaEmpresa, SedeEvento


class UsuarioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        nombre = obj.get_full_name().strip()
        return nombre or obj.username


class EventoBaseForm(forms.Form):
    nombre_evento = forms.CharField(
        label="Nombre del evento",
        max_length=180,
        widget=forms.TextInput(
            attrs={
                "class": "app-input",
                "placeholder": "Ej. Cena anual ACME",
                "autocomplete": "off",
            }
        ),
    )
    tipo_evento = forms.ChoiceField(
        label="Tipo de evento",
        choices=EventoBoda.TIPOS_EVENTO,
        required=False,
        widget=forms.Select(attrs={"class": "app-select"}),
    )
    fecha_inicio = forms.DateTimeField(
        label="Fecha y hora",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "app-input", "type": "datetime-local"},
        ),
    )
    fecha_fin = forms.DateTimeField(
        label="Fin",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"class": "app-input", "type": "datetime-local"},
        ),
    )
    cliente = UsuarioChoiceField(
        label="Cliente",
        queryset=get_user_model().objects.none(),
        required=False,
        empty_label="Por definir",
        widget=forms.Select(attrs={"class": "app-select"}),
    )
    planner = UsuarioChoiceField(
        label="Planner responsable",
        queryset=get_user_model().objects.none(),
        required=False,
        empty_label="Por definir",
        widget=forms.Select(attrs={"class": "app-select"}),
    )
    sede = forms.ModelChoiceField(
        label="Sede",
        queryset=SedeEvento.objects.none(),
        required=False,
        empty_label="Por definir",
        widget=forms.Select(attrs={"class": "app-select"}),
    )

    def __init__(self, *args, empresa, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        self.user = user

        User = get_user_model()
        cliente_ids = MembresiaEmpresa.objects.filter(
            empresa=empresa,
            rol="CLIENTE",
            activo=True,
        ).values_list("usuario_id", flat=True)
        planner_ids = MembresiaEmpresa.objects.filter(
            empresa=empresa,
            rol="WEDDING_PLANNER",
            activo=True,
        ).values_list("usuario_id", flat=True)

        self.fields["cliente"].queryset = User.objects.filter(
            id__in=cliente_ids,
            is_active=True,
        ).order_by("first_name", "last_name", "username")
        self.fields["planner"].queryset = User.objects.filter(
            id__in=planner_ids,
            is_active=True,
        ).order_by("first_name", "last_name", "username")
        self.fields["sede"].queryset = SedeEvento.objects.filter(
            empresa=empresa,
            activa=True,
        ).order_by("nombre")

        roles = set(
            MembresiaEmpresa.objects.filter(
                empresa=empresa,
                usuario=user,
                activo=True,
            ).values_list("rol", flat=True)
        )
        if "WEDDING_PLANNER" in roles and not roles.intersection({"ADMIN_EMPRESA", "VENTAS"}):
            self.fields["planner"].initial = user
            self.fields["planner"].disabled = True
            self.fields["planner"].help_text = "El evento quedará asignado a tu cuenta."

    def clean_nombre_evento(self):
        nombre = " ".join((self.cleaned_data.get("nombre_evento") or "").split()).strip()
        if not nombre:
            raise forms.ValidationError("Escribe un nombre para el evento.")
        return nombre

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("fecha_inicio")
        fin = cleaned.get("fecha_fin")
        if inicio and fin and fin < inicio:
            self.add_error("fecha_fin", "La fecha de fin no puede ser anterior al inicio.")
        return cleaned


class EventoCreateForm(EventoBaseForm):
    pass


class EventoEditForm(EventoBaseForm):
    def __init__(self, *args, evento, empresa, user, **kwargs):
        self.evento = evento
        initial = dict(kwargs.pop("initial", {}) or {})
        initial.setdefault("nombre_evento", evento.nombre_evento or evento.titulo_evento)
        initial.setdefault("tipo_evento", evento.tipo_evento)
        initial.setdefault("fecha_inicio", evento.fecha_inicio)
        initial.setdefault("fecha_fin", evento.fecha_fin)
        initial.setdefault("cliente", evento.clientes.first())
        initial.setdefault("planner", evento.wedding_planner)
        initial.setdefault("sede", evento.sede)
        kwargs["initial"] = initial
        super().__init__(*args, empresa=empresa, user=user, **kwargs)
