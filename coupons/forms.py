from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'product_name', 'product_link', 'category', 'description',
            'coupon_code', 'direct_link', 'has_expiry', 'expiry_date',
            'product_image', 'discount_amount', 'terms', 'instructions',
            'is_active'
        ]
        widgets = {
            'expiry_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'vDateField'}
            ),
            'description': forms.Textarea(attrs={'rows': 4}),
            'terms': forms.Textarea(attrs={'rows': 4}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'product_link': 'Link para a página do produto.',
            'direct_link': 'Link que já aplica o desconto automaticamente. Use no lugar do código de cupom, se disponível.',
            'coupon_code': 'Deixe em branco se estiver usando um link direto.',
            'has_expiry': 'Marque se o cupom tiver uma data de validade.',
            'expiry_date': 'A data de validade não pode ser no passado.',
            'discount_amount': 'Valor percentual do desconto (apenas números).'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lógica para desabilitar a data de validade se não for necessário
        if not self.instance.has_expiry:
            self.fields['expiry_date'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        has_expiry = cleaned_data.get('has_expiry')
        expiry_date = cleaned_data.get('expiry_date')
        coupon_code = cleaned_data.get('coupon_code')
        direct_link = cleaned_data.get('direct_link')

        if has_expiry and not expiry_date:
            self.add_error('expiry_date', 'Se o cupom tem validade, a data deve ser informada.')
        
        if not has_expiry and expiry_date:
            # Limpa a data de validade se a opção não estiver marcada
            cleaned_data['expiry_date'] = None

        if expiry_date and expiry_date < timezone.now().date():
            self.add_error('expiry_date', 'A data de validade não pode ser no passado.')

        if not coupon_code and not direct_link:
            raise ValidationError(
                'Você deve fornecer um "Código do Cupom" ou um "Link Direto com Desconto".',
                code='required'
            )
        
        return cleaned_data