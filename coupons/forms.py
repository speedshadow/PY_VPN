from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'product_name', 'product_link',
            'coupon_code', 'direct_link',
            'has_expiry', 'expiry_date',
            'is_active'
        ]
        widgets = {
            'expiry_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'min': timezone.now().date().isoformat()
                }
            ),
            'has_expiry': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': "document.getElementById('id_expiry_date').disabled = !this.checked;"
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        help_texts = {
            'product_link': 'Link para a página do produto',
            'direct_link': 'Link que já aplica o desconto automaticamente',
            'coupon_code': 'Deixe em branco se estiver usando link direto',
            'expiry_date': 'Opcional - Deixe em branco para cupom sem data de expiração'
        }

    def clean(self):
        cleaned_data = super().clean()
        has_expiry = cleaned_data.get('has_expiry')
        expiry_date = cleaned_data.get('expiry_date')
        
        if has_expiry and not expiry_date:
            self.add_error('expiry_date', 'Por favor, informe a data de validade')
        
        if expiry_date and expiry_date < timezone.now().date():
            self.add_error('expiry_date', 'A data de validade não pode ser no passado')
        
        return cleaned_data
        # widgets = {
        #     'product_name': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
        #     'product_link': forms.URLInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
        #     'coupon_code': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1', 'placeholder': 'Coupon Code'}),
        #     'direct_link': forms.URLInput(attrs={'class': 'w-full border rounded px-2 py-1', 'placeholder': 'Direct Link'}),
        #     'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full border rounded px-2 py-1'}),
        #     'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        #     'has_expiry': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        # }
        # labels = {
        #     'product_name': 'Nome do Produto/Serviço',
        #     'product_link': 'Link do Produto (URL)',
        #     'coupon_code': 'Código do Cupão (texto)',
        #     'direct_link': 'Link Direto de Desconto (URL)',
        #     'has_expiry': 'Tem data de validade?',
        #     'expiry_date': 'Data de Validade',
        #     'is_active': 'Está ativo?',
        # }
        # help_texts = {
        #     'product_link': 'Ex: https://www.loja.com/produto-exemplo',
        #     'coupon_code': 'Insira o código de texto a ser aplicado no checkout (ex: PROMO10). Deixe em branco se usar um Link Direto de Desconto.',
        #     'direct_link': 'Insira um URL que aplica o desconto automaticamente (ex: https://www.loja.com/desconto?codigo=XYZ). Se preenchido, este link será usado preferencialmente.',
        #     'expiry_date': 'Deixe em branco se não houver data de validade específica ou se "Tem data de validade?" não estiver marcado.',
        # }