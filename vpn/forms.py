from django import forms
from .models import VPN

class VPNForm(forms.ModelForm):
    devices_supported = forms.MultipleChoiceField(
        choices=VPN.DEVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Dispositivos Suportados"
    )

    class Meta:
        model = VPN
        exclude = ['speeds_by_country']
