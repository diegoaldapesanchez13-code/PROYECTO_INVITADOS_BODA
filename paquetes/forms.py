from django import forms

from catalogo.models import ServicioCatalogo
from organizaciones.models import SedeEvento

from .models import PaqueteBoda, PaqueteMediaComercial, PaqueteServicio, PropuestaEvento, PropuestaLinea


class PaqueteComercialForm(forms.ModelForm):
    class Meta:
        model = PaqueteBoda
        fields = [
            'nombre',
            'descripcion',
            'precio_base',
            'numero_personas_incluidas',
            'precio_adulto',
            'precio_nino',
            'cargo_fijo',
            'capacidad_minima_recomendada',
            'capacidad_maxima_recomendada',
            'duracion_evento',
            'portada',
            'pdf_comercial',
            'activo',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        if empresa is not None:
            self.instance.empresa = empresa

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa is not None:
            instance.empresa = self.empresa
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class PaqueteServicioForm(forms.ModelForm):
    class Meta:
        model = PaqueteServicio
        fields = ['servicio_catalogo', 'cantidad', 'orden', 'notas', 'incluido', 'obligatorio']
        widgets = {
            'notas': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, paquete=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.paquete = paquete
        if paquete is not None:
            self.instance.paquete = paquete
        self.fields['servicio_catalogo'].queryset = ServicioCatalogo.objects.none()
        if paquete and paquete.empresa_id:
            self.fields['servicio_catalogo'].queryset = ServicioCatalogo.objects.filter(
                empresa_id=paquete.empresa_id,
                activo=True,
            ).order_by('categoria', 'nombre')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.paquete is not None:
            instance.paquete = self.paquete
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class PaqueteMediaComercialForm(forms.ModelForm):
    class Meta:
        model = PaqueteMediaComercial
        fields = ['tipo', 'archivo', 'titulo', 'orden']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class PropuestaEventoForm(forms.ModelForm):
    class Meta:
        model = PropuestaEvento
        fields = ['sede', 'adultos', 'ninos', 'paquete', 'descuento', 'estado', 'notas_comerciales']
        widgets = {
            'notas_comerciales': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, empresa=None, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        self.evento = evento
        if empresa is not None:
            self.instance.empresa = empresa
        if evento is not None:
            self.instance.evento = evento
        self.fields['sede'].queryset = SedeEvento.objects.none()
        self.fields['paquete'].queryset = PaqueteBoda.objects.none()
        if empresa is not None:
            self.fields['sede'].queryset = SedeEvento.objects.filter(
                empresa=empresa,
                activa=True,
            ).order_by('nombre')
            paquetes = PaqueteBoda.objects.filter(empresa=empresa, activo=True).order_by('nombre')
            if self.instance and self.instance.pk and self.instance.paquete_id:
                paquetes = PaqueteBoda.objects.filter(empresa=empresa).filter(
                    pk=self.instance.paquete_id
                ) | paquetes
            self.fields['paquete'].queryset = paquetes.distinct()
        allowed_states = {'BORRADOR', 'PROPUESTA', 'EN_REVISION', 'CANCELADO'}
        if self.instance and self.instance.pk and self.instance.estado in {'ACEPTADO', 'CONTRATADO', 'CANCELADO'}:
            allowed_states.add(self.instance.estado)
        self.fields['estado'].choices = [
            choice
            for choice in self.fields['estado'].choices
            if choice[0] in allowed_states
        ]
        if self.instance and self.instance.pk and self.instance.estado in {'ACEPTADO', 'CONTRATADO', 'CANCELADO'}:
            for field in self.fields.values():
                field.disabled = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.empresa is not None:
            instance.empresa = self.empresa
        if self.evento is not None:
            instance.evento = self.evento
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class PropuestaLineaForm(forms.ModelForm):
    class Meta:
        model = PropuestaLinea
        fields = [
            'tipo',
            'servicio_catalogo',
            'nombre',
            'descripcion',
            'modo_precio',
            'tarifa',
            'cantidad',
            'valor_informativo',
            'orden',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, propuesta=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.propuesta = propuesta
        if propuesta is not None:
            self.instance.propuesta = propuesta
        self.fields['servicio_catalogo'].required = False
        self.fields['nombre'].required = False
        self.fields['nombre'].label = 'Nombre manual (solo fuera de catalogo)'
        self.fields['nombre'].help_text = (
            'Si eliges un servicio del catalogo, DIRTEC usara automaticamente su nombre. '
            'Solo escribe este campo para un servicio fuera de catalogo.'
        )
        self.fields['nombre'].widget.attrs.setdefault(
            'placeholder',
            'Solo para servicio fuera de catalogo',
        )
        self.fields['servicio_catalogo'].queryset = ServicioCatalogo.objects.none()
        if propuesta and propuesta.empresa_id:
            self.fields['servicio_catalogo'].queryset = ServicioCatalogo.objects.filter(
                empresa_id=propuesta.empresa_id,
                activo=True,
            ).order_by('categoria', 'nombre')

    def clean(self):
        cleaned = super().clean()
        servicio = cleaned.get('servicio_catalogo')
        nombre = (cleaned.get('nombre') or '').strip()
        if servicio:
            # El catalogo es la fuente canonica del nombre. No obligamos al
            # usuario a repetirlo ni aceptamos un alias enviado por POST.
            cleaned['nombre'] = servicio.nombre
        elif not nombre:
            self.add_error('nombre', 'Escribe un nombre para el servicio fuera de catalogo.')
        else:
            cleaned['nombre'] = nombre
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.propuesta is not None:
            instance.propuesta = self.propuesta
        if commit:
            instance.save()
            self.save_m2m()
        return instance
