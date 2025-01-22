from django import forms
from .models import PGNFile

class PGNFileForm(forms.ModelForm):
    class Meta:
        model = PGNFile
        fields = ['file']