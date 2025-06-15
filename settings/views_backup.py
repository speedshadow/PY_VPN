import os
import json
import logging
import shutil
import tempfile
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse, FileResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models_backup import BackupConfig, Backup, RestorePoint
from .forms_backup import BackupConfigForm, BackupForm, RestorePointForm, BackupUploadForm

logger = logging.getLogger(__name__)

# Helpers

def get_backup_directory():
    """Retorna o diretório de backup, criando se não existir"""
    backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def get_backup_filename(backup_type):
    """Gera um nome de arquivo para o backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{backup_type}_backup_{timestamp}.zip"

def get_database_backup_command():
    """Retorna o comando para fazer backup do banco de dados"""
    db = settings.DATABASES['default']
    engine = db['ENGINE']
    
    if 'postgresql' in engine:
        return f"pg_dump -h {db['HOST']} -U {db['USER']} -d {db['NAME']} -F c -b -f {get_backup_directory()}/db_backup.sql"
    elif 'mysql' in engine:
        return f"mysqldump -h {db['HOST']} -u {db['USER']} -p'{db['PASSWORD']}' {db['NAME']} > {get_backup_directory()}/db_backup.sql"
    else:  # SQLite
        db_path = db['NAME']
        return f"cp {db_path} {get_backup_directory()}/db_backup.sqlite3"

def create_zip_archive(files, output_filename):
    """Cria um arquivo ZIP com os arquivos fornecidos"""
    import zipfile
    from io import BytesIO
    
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if os.path.isfile(file):
                zf.write(file, os.path.basename(file))
    
    memory_file.seek(0)
    return memory_file

# Views

@login_required
@permission_required('settings.view_backupconfig')
def backup_dashboard(request):
    """Painel de controle de backups"""
    configs = BackupConfig.objects.all()
    recent_backups = Backup.objects.order_by('-created_at')[:5]
    
    # Estatísticas
    stats = {
        'total_backups': Backup.objects.count(),
        'total_size_mb': sum(b.backup_file.size for b in Backup.objects.all() if b.backup_file) / (1024 * 1024),
        'last_backup': Backup.objects.order_by('-created_at').first(),
        'next_scheduled': None
    }
    
    # Verifica se há tarefas agendadas
    try:
        task = PeriodicTask.objects.filter(task='settings.tasks.run_scheduled_backups').first()
        if task:
            stats['next_scheduled'] = task.date_changed + task.interval
    except Exception as e:
        logger.error(f"Erro ao verificar tarefas agendadas: {e}")
    
    context = {
        'configs': configs,
        'recent_backups': recent_backups,
        'stats': stats,
        'backup_dir': get_backup_directory(),
        'disk_usage': get_disk_usage(),
    }
    return render(request, 'dashboard/backup/dashboard.html', context)

@login_required
@permission_required('settings.add_backupconfig')
def backup_config_create(request, backup_type='full'):
    """Cria uma nova configuração de backup"""
    if request.method == 'POST':
        form = BackupConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.backup_type = backup_type
            config.save()
            messages.success(request, f'Configuração de backup {backup_type} criada com sucesso!')
            return redirect('backup_dashboard')
    else:
        initial = {'backup_type': backup_type}
        form = BackupConfigForm(initial=initial)
    
    return render(request, 'dashboard/backup/config_form.html', {
        'form': form,
        'title': f'Nova Configuração de Backup - {backup_type.upper()}'
    })

@login_required
@permission_required('settings.change_backupconfig')
def backup_config_edit(request, pk):
    """Edita uma configuração de backup existente"""
    config = get_object_or_404(BackupConfig, pk=pk)
    
    if request.method == 'POST':
        form = BackupConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuração de backup atualizada com sucesso!')
            return redirect('backup_dashboard')
    else:
        form = BackupConfigForm(instance=config)
    
    return render(request, 'dashboard/backup/config_form.html', {
        'form': form,
        'title': f'Editar Configuração - {config.get_backup_type_display()}'
    })

@login_required
@permission_required('settings.delete_backupconfig')
def backup_config_delete(request, pk):
    """Remove uma configuração de backup"""
    config = get_object_or_404(BackupConfig, pk=pk)
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuração de backup removida com sucesso!')
        return redirect('backup_dashboard')
    
    return render(request, 'dashboard/backup/confirm_delete.html', {
        'object': config,
        'title': 'Confirmar Exclusão de Configuração'
    })

@login_required
@permission_required('settings.add_backup')
def backup_create(request):
    """Cria um backup manual"""
    if request.method == 'POST':
        form = BackupForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            backup = form.save(commit=False)
            
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Backup do banco de dados (SQLite)
                    if backup.backup_type in ['full', 'db_only']:
                        db_path = settings.DATABASES['default']['NAME']
                        if os.path.exists(db_path):
                            shutil.copy(db_path, temp_dir)

                    # Backup dos arquivos de mídia
                    if backup.backup_type in ['full', 'media_only']:
                        media_path = settings.MEDIA_ROOT
                        if os.path.exists(media_path) and os.path.isdir(media_path):
                            shutil.copytree(media_path, os.path.join(temp_dir, 'media'))
                            
                    # Gera o nome do arquivo de backup
                    backup_dir = get_backup_directory()
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_filename_base = f"{backup.backup_type}_backup_{timestamp}"
                    backup_filename_zip = f"{backup_filename_base}.zip"
                    
                    # Cria o arquivo ZIP
                    archive_path = shutil.make_archive(
                        os.path.join(backup_dir, backup_filename_base),
                        'zip',
                        temp_dir
                    )

                    # Salva o arquivo no modelo
                    with open(archive_path, 'rb') as f:
                        backup.backup_file.save(backup_filename_zip, ContentFile(f.read()))
                    
                    backup.status = 'completed'
                    backup.size = backup.backup_file.size
                    backup.save()
                    
                    os.remove(archive_path)
                    
                    messages.success(request, 'Backup criado com sucesso!')
                    return redirect('settings:backup:backup_dashboard')
                
            except Exception as e:
                logger.error(f"Erro ao criar backup: {e}", exc_info=True)
                backup.status = 'failed'
                backup.notes = f"Erro: {str(e)}"
                backup.save()
                messages.error(request, f'Erro ao criar backup: {str(e)}')
    else:
        form = BackupForm(user=request.user)
    
    return render(request, 'dashboard/backup/backup_form.html', {
        'form': form,
        'title': 'Criar Backup Manual'
    })

@login_required
@permission_required('settings.view_backup')
def backup_list(request):
    """Lista todos os backups"""
    backups = Backup.objects.all().order_by('-created_at')
    return render(request, 'dashboard/backup/backup_list.html', {
        'backups': backups,
        'title': 'Lista de Backups'
    })

@login_required
@permission_required('settings.view_backup')
def backup_detail(request, pk):
    """Detalhes de um backup específico"""
    backup = get_object_or_404(Backup, pk=pk)
    restore_points = backup.restore_points.all()
    
    return render(request, 'dashboard/backup/backup_detail.html', {
        'backup': backup,
        'restore_points': restore_points,
        'title': f'Detalhes do Backup: {backup.name}'
    })

@login_required
@permission_required('settings.download_backup')
def backup_download(request, pk):
    """Faz o download de um backup"""
    backup = get_object_or_404(Backup, pk=pk)
    
    if not backup.backup_file:
        messages.error(request, 'Arquivo de backup não encontrado.')
        return redirect('backup_detail', pk=pk)
    
    try:
        response = FileResponse(backup.backup_file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(backup.backup_file.name)}"'
        return response
    except Exception as e:
        logger.error(f"Erro ao fazer download do backup {pk}: {e}", exc_info=True)
        messages.error(request, f'Erro ao fazer download do backup: {str(e)}')
        return redirect('backup_detail', pk=pk)


@login_required
@permission_required('settings.delete_backup')
def backup_delete(request, pk):
    """Remove um backup e seu arquivo associado."""
    backup = get_object_or_404(Backup, pk=pk)
    
    if request.method == 'POST':
        try:
            # Remove o arquivo de backup físico, se existir.
            if backup.backup_file and hasattr(backup.backup_file, 'path'):
                if os.path.exists(backup.backup_file.path):
                    os.remove(backup.backup_file.path)
            
            backup.delete()
            messages.success(request, f'O backup "{backup.name}" foi removido com sucesso!')
            return redirect('settings:backup:backup_dashboard')
        except Exception as e:
            logger.error(f"Erro ao remover o backup {pk}: {e}", exc_info=True)
            messages.error(request, f'Ocorreu um erro ao remover o backup: {str(e)}')
            return redirect('settings:backup:backup_detail', pk=pk)

    # Para requisições GET, exibe a página de confirmação.
    return render(request, 'dashboard/backup/backup_confirm_delete.html', {'backup': backup})

@login_required
@permission_required('settings.add_restorepoint')
def restore_point_create(request, backup_pk):
    """Restores the system from a given backup file."""
    backup = get_object_or_404(Backup, pk=backup_pk)

    if request.method == 'POST':
        if not backup.backup_file or not hasattr(backup.backup_file, 'path'):
            messages.error(request, 'Arquivo de backup não encontrado.')
            return redirect('settings:backup:backup_detail', pk=backup.pk)

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Unpack the archive
                shutil.unpack_archive(backup.backup_file.path, temp_dir)

                db_settings = settings.DATABASES['default']
                db_path = db_settings.get('NAME')
                media_path = settings.MEDIA_ROOT

                # Restore Database
                if backup.backup_type in ['full', 'db']:
                    backup_db_path = os.path.join(temp_dir, os.path.basename(db_path))
                    if os.path.exists(backup_db_path):
                        shutil.copy2(backup_db_path, db_path)
                        messages.info(request, 'Banco de dados restaurado com sucesso.')
                    else:
                        raise FileNotFoundError("Arquivo de banco de dados não encontrado no backup.")

                # Restore Media Files
                if backup.backup_type in ['full', 'media']:
                    backup_media_path = os.path.join(temp_dir, 'media')
                    if os.path.exists(backup_media_path):
                        # Be careful: this removes the current media folder content
                        if os.path.exists(media_path):
                            shutil.rmtree(media_path)
                        shutil.copytree(backup_media_path, media_path)
                        messages.info(request, 'Arquivos de mídia restaurados com sucesso.')
                    else:
                        raise FileNotFoundError("Pasta de mídia não encontrada no backup.")

            messages.success(request, f'Restauração do backup "{backup.name}" concluída com sucesso!')
            return redirect('settings:backup:backup_dashboard')

        except Exception as e:
            logger.error(f"Erro ao restaurar o backup {backup.pk}: {e}", exc_info=True)
            messages.error(request, f'Ocorreu um erro durante a restauração: {str(e)}')
            return redirect('settings:backup:backup_detail', pk=backup.pk)

    return render(request, 'dashboard/backup/restore_point_form.html', {'backup': backup})

@login_required
@permission_required('settings.view_restorepoint')
def restore_point_detail(request, pk):
    """Detalhes de um ponto de restauração"""
    restore_point = get_object_or_404(RestorePoint, pk=pk)
    
    return render(request, 'dashboard/backup/restore_detail.html', {
        'restore_point': restore_point,
        'title': f'Detalhes da Restauração: {restore_point}'
    })

@login_required
@permission_required('settings.upload_backup')
def backup_upload(request):
    """Faz upload de um arquivo de backup"""
    if request.method == 'POST':
        form = BackupUploadForm(request.POST, request.FILES)
        if form.is_valid():
            backup_file = form.cleaned_data['backup_file']
            backup_type = form.cleaned_data['backup_type']
            notes = form.cleaned_data.get('notes', '')
            
            try:
                # Salva o arquivo de backup
                fs = FileSystemStorage(location=get_backup_directory())
                filename = fs.save(backup_file.name, backup_file)
                file_path = fs.path(filename)
                
                # Cria o registro no banco de dados
                backup = Backup.objects.create(
                    name=f"Upload: {os.path.basename(filename)}",
                    backup_type=backup_type,
                    status='completed',
                    notes=notes,
                    created_by=request.user,
                    size=os.path.getsize(file_path)
                )
                
                # Move o arquivo para o local correto
                final_path = os.path.join('backups', filename)
                final_abs_path = os.path.join(settings.MEDIA_ROOT, final_path)
                os.makedirs(os.path.dirname(final_abs_path), exist_ok=True)
                os.rename(file_path, final_abs_path)
                
                # Atualiza o caminho do arquivo
                backup.backup_file = final_path
                backup.save()
                
                messages.success(request, 'Backup enviado com sucesso!')
                return redirect('backup_detail', pk=backup.pk)
                
            except Exception as e:
                logger.error(f"Erro ao fazer upload do backup: {e}", exc_info=True)
                # Remove o arquivo em caso de erro
                if 'file_path' in locals() and os.path.exists(file_path):
                    os.remove(file_path)
                messages.error(request, f'Erro ao fazer upload do backup: {str(e)}')
    else:
        form = BackupUploadForm()
    
    return render(request, 'dashboard/backup/backup_upload.html', {
        'form': form,
        'title': 'Enviar Backup'
    })

# API Views

@login_required
@permission_required('settings.view_backup')
@require_http_methods(["GET"])
def api_backup_status(request, pk):
    """Retorna o status de um backup (para atualização em tempo real)"""
    backup = get_object_or_404(Backup, pk=pk)
    return JsonResponse({
        'id': backup.id,
        'status': backup.status,
        'status_display': backup.get_status_display(),
        'progress': backup.progress if hasattr(backup, 'progress') else 100 if backup.status == 'completed' else 0,
        'notes': backup.notes,
        'size': backup.size,
        'size_display': f"{backup.size / (1024*1024):.2f} MB" if backup.size else '0 MB',
        'created_at': backup.created_at.isoformat(),
        'download_url': backup.backup_file.url if backup.backup_file else None,
    })

@login_required
@permission_required('settings.view_restorepoint')
@require_http_methods(["GET"])
def api_restore_status(request, pk):
    """Retorna o status de uma restauração (para atualização em tempo real)"""
    restore_point = get_object_or_404(RestorePoint, pk=pk)
    return JsonResponse({
        'id': restore_point.id,
        'status': restore_point.status,
        'status_display': restore_point.get_status_display(),
        'progress': restore_point.progress if hasattr(restore_point, 'progress') else 100 if restore_point.status == 'completed' else 0,
        'logs': restore_point.logs,
        'created_at': restore_point.created_at.isoformat(),
        'completed_at': restore_point.completed_at.isoformat() if restore_point.completed_at else None,
    })

# Tarefas agendadas

def setup_scheduled_backups():
    """Configura as tarefas agendadas de backup com base nas configurações"""
    try:
        from django_celery_beat.models import IntervalSchedule, PeriodicTask
        
        # Remove tarefas antigas
        PeriodicTask.objects.filter(
            task='settings.tasks.run_scheduled_backups'
        ).delete()
        
        # Cria uma tarefa para cada configuração ativa
        for config in BackupConfig.objects.filter(is_active=True):
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=1,
                period={
                    'daily': IntervalSchedule.DAYS,
                    'weekly': IntervalSchedule.DAYS,
                    'monthly': IntervalSchedule.DAYS,
                    'custom': IntervalSchedule.HOURS,
                }[config.frequency],
                defaults={
                    'every': {
                        'daily': 1,
                        'weekly': 7,
                        'monthly': 30,
                        'custom': max(1, config.custom_frequency or 24),
                    }[config.frequency]
                }
            )
            
            PeriodicTask.objects.create(
                interval=schedule,
                name=f'Backup {config.get_backup_type_display()} - {config.get_frequency_display()}',
                task='settings.tasks.run_scheduled_backups',
                args=json.dumps([config.id]),
                enabled=config.is_active,
            )
            
    except Exception as e:
        logger.error(f"Erro ao configurar backups agendados: {e}", exc_info=True)
        raise

# Utilitários

def get_disk_usage():
    """Retorna informações sobre o uso do disco"""
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        return {
            'total': total,
            'used': used,
            'free': free,
            'percent_used': (used / total) * 100,
            'total_gb': total / (1024**3),
            'used_gb': used / (1024**3),
            'free_gb': free / (1024**3),
        }
    except Exception as e:
        logger.error(f"Erro ao obter uso do disco: {e}", exc_info=True)
        return None

def cleanup_old_backups():
    """Remove backups antigos com base nas configurações de retenção"""
    try:
        for config in BackupConfig.objects.all():
            # Obtém os backups mais recentes, mantendo apenas o número máximo permitido
            backups = Backup.objects.filter(
                backup_type=config.backup_type
            ).order_by('-created_at')
            
            # Mantém apenas os N backups mais recentes
            if config.max_backups > 0:
                for backup in backups[config.max_backups:]:
                    backup.delete()
                    
    except Exception as e:
        logger.error(f"Erro ao limpar backups antigos: {e}", exc_info=True)
        raise
