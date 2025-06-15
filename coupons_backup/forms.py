from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = '__all__'
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