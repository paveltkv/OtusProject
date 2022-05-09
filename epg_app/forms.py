from django import forms
from epg_app.models import Epg


class EpgAddForm(forms.ModelForm):
    class Meta:
        model = Epg
        fields = ('name', 'url', 'logos_url')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'logos_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
