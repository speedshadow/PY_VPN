from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Nome"}),
            "email": forms.EmailInput(attrs={"class": "input", "placeholder": "Email"}),
            "subject": forms.TextInput(attrs={"class": "input", "placeholder": "Assunto"}),
            "message": forms.Textarea(attrs={"class": "textarea", "placeholder": "Mensagem", "rows": 5}),
        }
