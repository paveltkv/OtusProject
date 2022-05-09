from django import forms
from django.forms import ModelForm

from playlist_app.models import PlayList
from user_app.models import CustomUser


class PlayListRulesEditForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ('playlist_rules', 'icons_source')
        labels = {'playlist_rules': '', }

        CHOICES = [('1', 'First'), ('2', 'Second')]
        blogs_cat = forms.ModelChoiceField(queryset=CustomUser.objects.all(), empty_label="None",
                                           to_field_name="icons_source")
        widgets = {
            'playlist_rules': forms.Textarea(attrs={'placeholder': 'Playlist rules'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            # print(name)
            # print(field)
            field.widget.attrs['class'] = 'model-form'


class PlayListForm(forms.ModelForm):
    class Meta:
        model = PlayList
        fields = ('name', 'url', 'marker')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'marker': forms.TextInput(attrs={'class': 'form-control'}),
        }
