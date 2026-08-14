from django import forms

from .models import ServicioCatalogo, ServicioCatalogoArchivo


class ServicioCatalogoForm(forms.ModelForm):
    class Meta:
        model = ServicioCatalogo
        fields = ['nombre', 'categoria', 'descripcion', 'unidad', 'activo', 'imagen_principal']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 5}),
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


class ServicioCatalogoArchivoForm(forms.ModelForm):
    class Meta:
        model = ServicioCatalogoArchivo
        fields = ['tipo', 'archivo', 'titulo', 'orden']

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance
