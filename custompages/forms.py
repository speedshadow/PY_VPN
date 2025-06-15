from django import forms
from .models import CustomPage

class CustomPageForm(forms.ModelForm):
    class Meta:
        model = CustomPage
        fields = ['title', 'slug', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'slug': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1', 'placeholder': 'Slug (ex: about, privacy)'}),
            'content': forms.Textarea(attrs={'class': 'w-full border rounded px-2 py-1', 'rows': 8}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
