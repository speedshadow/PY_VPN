from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models_backup import BackupConfig, Backup, RestorePoint

class BackupConfigForm(forms.ModelForm):
    class Meta:
        model = BackupConfig
        fields = '__all__'
        widgets = {
            'custom_frequency': forms.NumberInput(attrs={'min': 1, 'max': 8760}),
            'max_backups': forms.NumberInput(attrs={'min': 1, 'max': 100}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        custom_frequency = cleaned_data.get('custom_frequency')
        
        if frequency == 'custom' and not custom_frequency:
            self.add_error('custom_frequency', 'Este campo é obrigatório quando a frequência é personalizada.')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            # Garante que apenas uma configuração de cada tipo exista
            BackupConfig.objects.filter(backup_type=instance.backup_type).exclude(pk=instance.pk).delete()
            instance.save()
        
        return instance


class BackupForm(forms.ModelForm):
    class Meta:
        model = Backup
        fields = ['name', 'backup_type', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'backup_type': forms.Select(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class RestorePointForm(forms.ModelForm):
    class Meta:
        model = RestorePoint
        fields = ['backup', 'restore_path']
        widgets = {
            'restore_path': forms.TextInput(attrs={'placeholder': '/caminho/para/restauracao'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['backup'].queryset = Backup.objects.filter(status='completed')
    
    def clean_restore_path(self):
        restore_path = self.cleaned_data.get('restore_path')
        if not restore_path.startswith('/'):
            raise ValidationError('O caminho deve começar com /')
        return restore_path
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance


class BackupUploadForm(forms.Form):
    backup_file = forms.FileField(
        label='Arquivo de Backup',
        help_text='Selecione um arquivo de backup (.zip, .tar.gz, .sql, .json)',
        widget=forms.FileInput(attrs={'accept': '.zip,.tar.gz,.sql,.json'})
    )
    backup_type = forms.ChoiceField(
        label='Tipo de Backup',
        choices=BackupConfig.BACKUP_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        label='Notas',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Adicione notas sobre este backup'})
    )
    
    def clean_backup_file(self):
        backup_file = self.cleaned_data.get('backup_file')
        if backup_file:
            valid_extensions = ['.zip', '.tar.gz', '.sql', '.json']
            ext = os.path.splitext(backup_file.name)[1].lower()
            if ext == '.gz' and backup_file.name.lower().endswith('.tar.gz'):
                ext = '.tar.gz'
            
            if ext not in valid_extensions:
                raise ValidationError('Tipo de arquivo não suportado. Use .zip, .tar.gz, .sql ou .json')
            
            # Limita o tamanho do arquivo a 500MB
            max_size = 500 * 1024 * 1024  # 500MB
            if backup_file.size > max_size:
                raise ValidationError(f'O arquivo é muito grande. O tamanho máximo permitido é {max_size/1024/1024}MB')
        
        return backup_file
