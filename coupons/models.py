from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Coupon(models.Model):
    # Informações básicas
    product_name = models.CharField('Nome do Produto', max_length=200)
    product_link = models.URLField('Link do Produto', max_length=500, blank=True, null=True)
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name='Categoria'
    )
    description = models.TextField('Descrição', blank=True, null=True)
    views_count = models.PositiveIntegerField('Visualizações', default=0)
    
    # Código e links
    coupon_code = models.CharField('Código do Cupom', max_length=100, blank=True, null=True)
    direct_link = models.URLField('Link Direto com Desconto', max_length=500, blank=True, null=True)
    
    # Controle de validade
    has_expiry = models.BooleanField('Tem data de validade?', default=False)
    expiry_date = models.DateField('Data de Validade', blank=True, null=True)
    
    # Imagem e detalhes adicionais
    product_image = models.ImageField('Imagem do Produto', upload_to='coupons/products/', blank=True, null=True)
    discount_amount = models.PositiveIntegerField('Valor do Desconto (%)', blank=True, null=True)
    terms = models.TextField('Termos e Condições', blank=True, null=True)
    instructions = models.TextField('Instruções de Uso', blank=True, null=True)
    click_count = models.PositiveIntegerField('Número de Cliques', default=0)
    
    # Status
    is_active = models.BooleanField('Ativo', default=True)
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_coupons',
        verbose_name='Criado por'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_coupons',
        verbose_name='Atualizado por'
    )
    
    class Meta:
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product_name} - {self.coupon_code if self.coupon_code else 'Sem Código'}"
        
    @property
    def is_expired(self):
        """Verifica se o cupom expirou"""
        if not self.has_expiry or not self.expiry_date:
            return False
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
        
    def increment_click_count(self):
        """Incrementa o contador de cliques"""
        self.click_count = models.F('click_count') + 1
        self.save(update_fields=['click_count'])
        
    def increment_views_count(self):
        """Incrementa o contador de visualizações"""
        self.views_count = models.F('views_count') + 1
        self.save(update_fields=['views_count'])
        
    # Método get_absolute_url removido para desativar a visualização individual de cupons
