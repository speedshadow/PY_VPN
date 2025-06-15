from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'slug': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1', 'placeholder': 'Slug (ex: best-vpns-for-gaming)'}),
        }
