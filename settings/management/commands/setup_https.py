import os
import subprocess
import socket
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

try:
    import paramiko
except ImportError:
    # Provide a helpful message if paramiko is not installed
    paramiko = None

class Command(BaseCommand):
    help = 'Configura HTTPS em um servidor REMOTO usando Certbot via SSH (Let\'s Encrypt). Requer Paramiko.'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email para notificações de renovação do Certbot')
        parser.add_argument('--domain', type=str, help='Domínio principal a ser configurado (ex: exemplo.com)')
        parser.add_argument('--dry-run', action='store_true',
                          help='Executar Certbot em modo de teste (não salva certificados nem altera config)')
        
        # Argumentos para conexão SSH remota
        parser.add_argument('--remote-ip', type=str, required=True, help='IP do servidor remoto VPS/VPN')
        parser.add_argument('--remote-user', type=str, required=True, help='Usuário para login SSH no servidor remoto (ex: root)')
        parser.add_argument('--ssh-key-file', type=str, default=None,
                          help='Caminho para o arquivo da chave SSH privada. Se não fornecido, tenta autenticação via agente SSH ou chaves padrão.')

    def handle(self, *args, **options):
        if paramiko is None:
            raise CommandError(
                'A biblioteca `paramiko` é necessária para executar este comando remotamente. ' 
                'Por favor, instale-a com: pip install paramiko'
            )

        email = options.get('email')
        domain = options.get('domain')
        dry_run = options.get('dry_run')
        remote_ip = options.get('remote_ip')
        remote_user = options.get('remote_user')
        ssh_key_file = options.get('ssh_key_file')

        if not domain:
            domain = socket.getfqdn()
            self.stdout.write(self.style.NOTICE(f'Usando domínio detectado: {domain}'))

        if not email:
            from ...models import SiteSettings
            try:
                site_settings = SiteSettings.objects.first()
                if site_settings and site_settings.contact_email:
                    email = site_settings.contact_email
                    self.stdout.write(self.style.NOTICE(f'Usando email do site: {email}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Não foi possível obter email das configurações: {e}'))

        if not email:
            raise CommandError('Email é obrigatório. Use --email ou configure em SiteSettings.contact_email')

        # Comando Certbot a ser executado no servidor remoto
        # O plugin Nginx lida com a configuração do Nginx e o webroot para desafios,
        # além de recarregar o Nginx após a instalação/renovação.
        certbot_command_parts = [
            'sudo', 'certbot', '--nginx',
            '-d', domain,
            '--email', email,
            '--agree-tos',
            '--non-interactive',
            '--redirect',      # Adiciona redirecionamento HTTP -> HTTPS automaticamente
            '--keep-until-expiring',
            '--expand'
        ]

        if dry_run:
            certbot_command_parts.append('--dry-run')
            self.stdout.write(self.style.WARNING('Modo de teste (dry-run) do Certbot ativado.'))
        
        certbot_command_str_remote = ' '.join(certbot_command_parts)

        self.stdout.write(self.style.SUCCESS(f'Tentando conectar a {remote_user}@{remote_ip}...'))
        self.stdout.write(f'Comando a ser executado remotamente: {certbot_command_str_remote}')

        ssh = None
        remote_exit_status = -1
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Menos seguro; considere usar um known_hosts
            
            connect_args = {
                'hostname': remote_ip,
                'username': remote_user
            }
            if ssh_key_file:
                connect_args['key_filename'] = ssh_key_file
            
            ssh.connect(**connect_args)
            self.stdout.write(self.style.SUCCESS('Conectado ao servidor remoto.'))
            self.stdout.write(self.style.SUCCESS('Executando comando Certbot...'))

            stdin, stdout, stderr = ssh.exec_command(certbot_command_str_remote)
            
            remote_stdout = stdout.read().decode()
            remote_stderr = stderr.read().decode()
            remote_exit_status = stdout.channel.recv_exit_status()

            if remote_stdout:
                self.stdout.write(self.style.SUCCESS('Saída do Certbot (stdout remoto):'))
                self.stdout.write(remote_stdout)
            if remote_stderr:
                self.stdout.write(self.style.WARNING('Erros do Certbot (stderr remoto):'))
                self.stdout.write(remote_stderr)

            if remote_exit_status == 0:
                self.stdout.write(self.style.SUCCESS('Comando Certbot executado com sucesso no servidor remoto!'))
            else:
                self.stdout.write(self.style.ERROR(f'Comando Certbot falhou no servidor remoto com código de saída: {remote_exit_status}'))

        except paramiko.AuthenticationException:
            self.stdout.write(self.style.ERROR('Falha na autenticação SSH. Verifique o usuário, IP e chave SSH.'))
            raise CommandError('Falha na autenticação SSH.')
        except paramiko.SSHException as ssh_ex:
            self.stdout.write(self.style.ERROR(f'Erro de SSH: {str(ssh_ex)}'))
            raise CommandError(f'Erro de SSH: {str(ssh_ex)}')
        except socket.error as sock_ex:
            self.stdout.write(self.style.ERROR(f'Erro de Socket/Rede ao conectar: {str(sock_ex)}'))
            raise CommandError(f'Erro de Socket/Rede: {str(sock_ex)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Um erro inesperado ocorreu: {str(e)}'))
            raise CommandError(f'Erro inesperado: {str(e)}')
        finally:
            if ssh:
                ssh.close()
                self.stdout.write(self.style.NOTICE('Conexão SSH fechada.'))

        # Se o comando remoto foi bem-sucedido (exit_status == 0)
        if remote_exit_status == 0:
            from ...models import SiteSettings # Importa localmente para evitar problemas se models.py não estiver pronto
            try:
                site_settings = SiteSettings.objects.first()
                if site_settings:
                    site_settings.enable_https = True
                    site_settings.save()
                    self.stdout.write(self.style.SUCCESS('Configuração local enable_https atualizada no painel.'))
                else:
                    self.stdout.write(self.style.WARNING('Nenhuma instância de SiteSettings encontrada para atualizar enable_https.'))
            except Exception as db_error:
                self.stdout.write(self.style.WARNING(f'Não foi possível atualizar SiteSettings localmente: {db_error}'))
            # Não há 'return' explícito aqui, o handle do BaseCommand não espera um valor de retorno específico para sucesso/falha assim.
            # A ausência de CommandError implica sucesso para o Django.
        else:
            # Se remote_exit_status não for 0, ou se ocorreu uma exceção antes de definir remote_exit_status
            raise CommandError('Falha na configuração remota do HTTPS. Verifique os logs acima.')
