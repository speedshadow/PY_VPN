from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

class ComplianceSettings(models.Model):
    # GDPR/LGPD
    is_gdpr_compliant = models.BooleanField('Conformidade com GDPR/LGPD', default=True)
    data_controller = models.CharField('Controlador de Dados', max_length=255, 
                                      default=settings.SITE_NAME)
    data_protection_officer = models.CharField('Encarregado de Dados (DPO)', max_length=255, blank=True)
    dpo_email = models.EmailField('E-mail do DPO', blank=True)
    privacy_policy = CKEditor5Field('Política de Privacidade', blank=True, config_name='extends')
    terms_of_service = CKEditor5Field('Termos de Serviço', blank=True, config_name='extends')
    cookie_policy = CKEditor5Field('Política de Cookies', blank=True, config_name='extends')
    data_retention_days = models.PositiveIntegerField('Retenção de Dados (dias)', default=365,
                                                     help_text='Número de dias para reter dados de usuários inativos')
    
    # Cookies
    cookie_consent_enabled = models.BooleanField('Ativar Consentimento de Cookies', default=True)
    cookie_consent_message = models.TextField('Mensagem de Consentimento', 
                                             default='Nós usamos cookies para melhorar sua experiência. Ao continuar navegando, você concorda com nossa Política de Privacidade.')
    cookie_necessary = models.BooleanField('Cookies Necessários', default=True)
    cookie_analytics = models.BooleanField('Cookies de Análise', default=False)
    cookie_marketing = models.BooleanField('Cookies de Marketing', default=False)
    cookie_preferences = models.BooleanField('Salvar Preferências', default=True)
    
    # CCPA (California Consumer Privacy Act)
    is_ccpa_compliant = models.BooleanField('Conformidade com CCPA', default=False)
    ccpa_do_not_sell_link = models.BooleanField('Link "Não Vender Minhas Informações"', default=False)
    
    # Outras Conformidades
    age_restriction = models.PositiveIntegerField('Restrição de Idade', default=13,
                                                 help_text='Idade mínima para usar o site')
    
    # Auditoria
    last_audit_date = models.DateField('Última Auditoria', null=True, blank=True)
    next_audit_date = models.DateField('Próxima Auditoria', null=True, blank=True)
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Conformidade'
        verbose_name_plural = 'Configurações de Conformidade'

    def __str__(self):
        return 'Configurações de Conformidade'


class DataRequest(models.Model):
    REQUEST_TYPES = [
        ('access', 'Acesso aos Dados'),
        ('deletion', 'Exclusão de Dados'),
        ('rectification', 'Retificação de Dados'),
        ('portability', 'Portabilidade de Dados'),
        ('restriction', 'Restrição de Processamento'),
        ('objection', 'Oposição ao Processamento'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('rejected', 'Rejeitado'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                           related_name='data_requests')
    request_type = models.CharField('Tipo de Solicitação', max_length=20, choices=REQUEST_TYPES)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField('Descrição')
    response = models.TextField('Resposta', blank=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='processed_requests')
    processed_at = models.DateTimeField('Processado em', null=True, blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Solicitação de Dados'
        verbose_name_plural = 'Solicitações de Dados'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_request_type_display()}"  
