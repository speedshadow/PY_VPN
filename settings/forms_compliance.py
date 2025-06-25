from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from .models_compliance import ComplianceSettings, DataRequest

class ComplianceSettingsForm(forms.ModelForm):
    class Meta:
        model = ComplianceSettings
        fields = '__all__'
        widgets = {
            'privacy_policy': forms.Textarea(attrs={'class': 'ckeditor'}),
            'terms_of_service': forms.Textarea(attrs={'class': 'ckeditor'}),
            'cookie_policy': forms.Textarea(attrs={'class': 'ckeditor'}),
            'cookie_consent_message': forms.Textarea(attrs={'rows': 3}),
            'data_retention_days': forms.NumberInput(attrs={'min': 1, 'max': 3650}),  # Max 10 anos
            'age_restriction': forms.NumberInput(attrs={'min': 1, 'max': 120}),
            'last_audit_date': forms.DateInput(attrs={'type': 'date'}),
            'next_audit_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes Tailwind para melhor aparência
        for field in self.fields:
            if field not in ['privacy_policy', 'terms_of_service', 'cookie_policy']:
                self.fields[field].widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
                })
    
    def clean(self):
        cleaned_data = super().clean()
        last_audit = cleaned_data.get('last_audit_date')
        next_audit = cleaned_data.get('next_audit_date')
        
        if last_audit and next_audit and last_audit > next_audit:
            self.add_error('next_audit_date', 'A próxima data de auditoria deve ser posterior à última auditoria.')
        
        return cleaned_data


class DataRequestForm(forms.ModelForm):
    class Meta:
        model = DataRequest
        fields = ['request_type', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva sua solicitação em detalhes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and not user.is_staff:
            # Para usuários não administradores, limpa as opções de resposta
            self.fields['request_type'].choices = [
                ('access', 'Acesso aos Meus Dados'),
                ('deletion', 'Excluir Meus Dados'),
                ('rectification', 'Corrigir Meus Dados'),
                ('portability', 'Solicitar Portabilidade de Dados'),
            ]
        
        # Adiciona classes Tailwind
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            })


class DataRequestResponseForm(forms.ModelForm):
    class Meta:
        model = DataRequest
        fields = ['status', 'response']
        widgets = {
            'response': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Digite sua resposta aqui...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra apenas status relevantes para resposta
        self.fields['status'].choices = [
            ('in_progress', 'Em Andamento'),
            ('completed', 'Concluído'),
            ('rejected', 'Rejeitado'),
        ]
        
        # Adiciona classes Tailwind
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            })


class CookieConsentForm(forms.Form):
    necessary = forms.BooleanField(
        label='Necessários',
        initial=True,
        disabled=True,
        required=True,
        help_text='Cookies essenciais para o funcionamento do site.'
    )
    
    preferences = forms.BooleanField(
        label='Preferências',
        required=False,
        help_text='Lembrar minhas configurações e preferências.'
    )
    
    analytics = forms.BooleanField(
        label='Análise',
        required=False,
        help_text='Ajudar-nos a melhorar o site coletando informações de uso.'
    )
    
    marketing = forms.BooleanField(
        label='Marketing',
        required=False,
        help_text='Personalizar anúncios com base nos meus interesses.'
    )
    
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        if 'consent' in initial:
            consent = initial.pop('consent')
            initial.update({
                'necessary': True,  # Sempre necessário
                'preferences': consent.get('preferences', False),
                'analytics': consent.get('analytics', False),
                'marketing': consent.get('marketing', False),
            })
        super().__init__(*args, **kwargs)
        
        # Adiciona classes Tailwind
        for field_name, field in self.fields.items():
            if field_name != 'necessary':  # Mantém o necessário desabilitado
                field.widget.attrs.update({
                    'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                })
