import os
import json
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import FileSystemStorage

def backup_upload_path(instance, filename):
    return f'backups/{instance.backup_type}/{filename}'

class BackupConfig(models.Model):
    BACKUP_TYPES = [
        ('full', 'Backup Completo'),
        ('db', 'Apenas Banco de Dados'),
        ('media', 'Apenas Mídia'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Diário'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
        ('custom', 'Personalizado'),
    ]
    
    backup_type = models.CharField('Tipo de Backup', max_length=10, choices=BACKUP_TYPES, default='full')
    frequency = models.CharField('Frequência', max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    custom_frequency = models.PositiveIntegerField('Frequência Personalizada (horas)', null=True, blank=True)
    keep_local = models.BooleanField('Manter localmente', default=True)
    max_backups = models.PositiveIntegerField('Número máximo de backups', default=5)
    last_run = models.DateTimeField('Última execução', null=True, blank=True)
    next_run = models.DateTimeField('Próxima execução', null=True, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    def __str__(self):
        return f"{self.get_backup_type_display()} - {self.get_frequency_display()}"
    
    class Meta:
        verbose_name = 'Configuração de Backup'
        verbose_name_plural = 'Configurações de Backup'


class Backup(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
        ('restored', 'Restaurado'),
    ]
    
    name = models.CharField('Nome', max_length=255)
    backup_file = models.FileField('Arquivo de Backup', upload_to=backup_upload_path, max_length=500)
    backup_type = models.CharField('Tipo', max_length=10, choices=BackupConfig.BACKUP_TYPES)
    size = models.BigIntegerField('Tamanho (bytes)', default=0)
    status = models.CharField('Status', max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField('Notas', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if self.backup_file:
            self.size = self.backup_file.size
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Remove o arquivo físico ao excluir o registro
        if self.backup_file:
            if os.path.isfile(self.backup_file.path):
                os.remove(self.backup_file.path)
        super().delete(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Backup'
        verbose_name_plural = 'Backups'
        ordering = ['-created_at']


class RestorePoint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('failed', 'Falhou'),
    ]
    
    backup = models.ForeignKey(Backup, on_delete=models.CASCADE, related_name='restore_points')
    status = models.CharField('Status', max_length=15, choices=STATUS_CHOICES, default='pending')
    restore_path = models.TextField('Caminho de Restauração')
    logs = models.TextField('Logs', blank=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    completed_at = models.DateTimeField('Concluído em', null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Restauração de {self.backup.name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = 'Ponto de Restauração'
        verbose_name_plural = 'Pontos de Restauração'
        ordering = ['-created_at']
