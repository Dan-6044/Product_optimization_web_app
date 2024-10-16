from django import forms
from .models import OptimizationData

class OptimizationDataForm(forms.ModelForm):
    class Meta:
        model = OptimizationData
        fields = ['file']
