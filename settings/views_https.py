import os
import socket
import subprocess
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from .models import SiteSettings

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def https_setup_wizard(request):
    context = {
        'current_domain': request.get_host().split(':')[0],
        'certbot_installed': is_certbot_installed(),
        'nginx_installed': is_nginx_installed(),
        'current_ip': get_public_ip(),
    }
    
    if request.method == 'POST':
        domain = request.POST.get('domain')
        email = request.POST.get('email')
        remote_ip = request.POST.get('remote_ip')
        remote_user = request.POST.get('remote_user')
        ssh_key_file = request.POST.get('ssh_key_file')
        dry_run = 'dry_run' in request.POST

        if not all([domain, email, remote_ip, remote_user, ssh_key_file]):
            messages.error(request, 'Todos os campos são obrigatórios: Domínio, Email, IP Remoto, Usuário Remoto e Caminho da Chave SSH.')
            return render(request, self.template_name, context)

        # Construir o comando
        command_args = [
            'setup_https',
            '--domain', domain,
            '--email', email,
            '--remote-ip', remote_ip,
            '--remote-user', remote_user,
            '--ssh-key-file', ssh_key_file,
        ]
        if dry_run:
            command_args.append('--dry-run')

        try:
            # Usar um buffer para capturar a saída do comando
            output_buffer = io.StringIO()
            print(f"Calling manage.py setup_https with args: {command_args}") # Debug log
            call_command(*command_args, stdout=output_buffer, stderr=output_buffer)
            output = output_buffer.getvalue()
            # Analisar a saída para determinar sucesso ou falha de forma mais robusta seria ideal
            # Por agora, vamos assumir sucesso se não houver CommandError
            if "CommandError" not in output and ("Successfully" in output or "success" in output.lower() or "Congratulations" in output):
                messages.success(request, f'Processo de configuração HTTPS concluído. Verifique a saída abaixo.')
                return redirect('settings_edit')
            else:
                messages.error(request, f'Erro ao configurar SSL: {result.stderr}')
                
        except Exception as e:
            messages.error(request, f'Erro ao configurar SSL: {str(e)}')
    
    return render(request, 'admin/settings/https_setup.html', context)

def is_certbot_installed():
    try:
        result = subprocess.run(['which', 'certbot'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def is_nginx_installed():
    try:
        result = subprocess.run(['which', 'nginx'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_public_ip():
    try:
        import requests
        return requests.get('https://api.ipify.org').text
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return 'Não foi possível determinar o IP público'

def verify_domain_resolution(domain):
    try:
        public_ip = get_public_ip()
        resolved_ips = socket.gethostbyname_ex(domain)[2]
        return public_ip in resolved_ips
    except:
        return False

def setup_auto_renewal():
    """Configura a renovação automática dos certificados"""
    try:
        # Verifica se já existe um agendamento
        result = subprocess.run(
            ['crontab', '-l'], 
            capture_output=True, 
            text=True
        )
        
        cron_content = result.stdout if result.returncode == 0 else ''
        
        # Adiciona a linha de renovação se não existir
        if 'certbot renew' not in cron_content:
            cron_entry = '0 0,12 * * * root /usr/bin/certbot renew --quiet --deploy-hook "systemctl reload nginx"\n'
            with open('/etc/cron.d/certbot', 'w') as f:
                f.write(cron_entry)
            
            return True
        return False
    except Exception as e:
        print(f"Erro ao configurar renovação automática: {e}")
        return False
