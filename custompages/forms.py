from django import forms
from .models import CustomPage
from django_ckeditor_5.widgets import CKEditor5Widget

class CustomPageForm(forms.ModelForm):
    class Meta:
        model = CustomPage
        fields = ['title', 'slug', 'content', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'slug': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1', 'placeholder': 'O slug será gerado automaticamente'}),
            'content': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name='default'
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
