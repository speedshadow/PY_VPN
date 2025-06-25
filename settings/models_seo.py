from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class SEOSettings(models.Model):
    meta_title = models.CharField('Meta Título', max_length=100, default=settings.SITE_NAME)
    meta_description = models.TextField('Meta Descrição', blank=True)
    meta_keywords = models.TextField('Palavras-chave', blank=True, help_text='Separadas por vírgula')
    meta_author = models.CharField('Autor', max_length=100, blank=True)
    meta_robots = models.CharField('Robôs', max_length=100, default='index, follow')
    canonical_url = models.URLField('URL Canônica', blank=True)
    og_title = models.CharField('Open Graph Título', max_length=100, blank=True)
    og_description = models.TextField('Open Graph Descrição', blank=True)
    og_image = models.ImageField('Open Graph Imagem', upload_to='seo/', blank=True, null=True)
    twitter_card = models.CharField('Twitter Card', max_length=50, default='summary_large_image')
    twitter_site = models.CharField('Twitter @site', max_length=100, blank=True)
    twitter_creator = models.CharField('Twitter @creator', max_length=100, blank=True)
    structured_data = models.TextField('Dados Estruturados (JSON-LD)', blank=True)
    sitemap_priority = models.FloatField('Prioridade do Sitemap', default=0.5, 
                                       help_text='Valor entre 0.0 e 1.0')
    sitemap_changefreq = models.CharField('Frequência de Mudança', max_length=20, 
                                        default='weekly',
                                        choices=[
                                            ('always', 'Sempre'),
                                            ('hourly', 'A cada hora'),
                                            ('daily', 'Diariamente'),
                                            ('weekly', 'Semanalmente'),
                                            ('monthly', 'Mensalmente'),
                                            ('yearly', 'Anualmente'),
                                            ('never', 'Nunca')
                                        ])
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração SEO'
        verbose_name_plural = 'Configurações SEO'

    def __str__(self):
        return 'Configurações SEO do Site'


class PageSEO(models.Model):
    PAGE_TYPES = [
        ('home', 'Página Inicial'),
        ('blog', 'Blog'),
        ('post', 'Post do Blog'),
        ('category', 'Categoria'),
        ('page', 'Página'),
        ('product', 'Produto'),
        ('custom', 'Personalizado'),
    ]
    
    page_type = models.CharField('Tipo de Página', max_length=20, choices=PAGE_TYPES, unique=True)
    meta_title = models.CharField('Meta Título', max_length=100, blank=True)
    meta_description = models.TextField('Meta Descrição', blank=True)
    meta_keywords = models.TextField('Palavras-chave', blank=True)
    meta_robots = models.CharField('Robôs', max_length=100, default='index, follow')
    canonical_url = models.URLField('URL Canônica', blank=True)
    og_title = models.CharField('Open Graph Título', max_length=100, blank=True)
    og_description = models.TextField('Open Graph Descrição', blank=True)
    og_image = models.ImageField('Open Graph Imagem', upload_to='seo/pages/', blank=True, null=True)
    structured_data = models.TextField('Dados Estruturados (JSON-LD)', blank=True)
    sitemap_include = models.BooleanField('Incluir no Sitemap', default=True)
    sitemap_priority = models.FloatField('Prioridade', default=0.5, 
                                       help_text='Valor entre 0.0 e 1.0')
    sitemap_changefreq = models.CharField('Frequência de Mudança', max_length=20, 
                                        default='weekly',
                                        choices=[
                                            ('always', 'Sempre'),
                                            ('hourly', 'A cada hora'),
                                            ('daily', 'Diariamente'),
                                            ('weekly', 'Semanalmente'),
                                            ('monthly', 'Mensalmente'),
                                            ('yearly', 'Anualmente'),
                                            ('never', 'Nunca')
                                        ])
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'SEO por Página'
        verbose_name_plural = 'SEO por Páginas'
        ordering = ['page_type']

    def __str__(self):
        return f'SEO - {self.get_page_type_display()}'


class XMLSitemap(models.Model):
    url = models.CharField('URL Path', max_length=2000, help_text='Enter the path relative to the site, e.g., /about/ or /products/my-product/. Must start with a slash.')
    priority = models.FloatField('Prioridade', default=0.5)
    changefreq = models.CharField('Frequência de Mudança', max_length=20, 
                                default='weekly',
                                choices=[
                                    ('always', 'Sempre'),
                                    ('hourly', 'A cada hora'),
                                    ('daily', 'Diariamente'),
                                    ('weekly', 'Semanalmente'),
                                    ('monthly', 'Mensalmente'),
                                    ('yearly', 'Anualmente'),
                                    ('never', 'Nunca')
                                ])
    lastmod = models.DateTimeField('Última Modificação', auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'URL do Sitemap'
        verbose_name_plural = 'URLs do Sitemap'
        ordering = ['-priority', 'url']

    def __str__(self):
        return self.url
