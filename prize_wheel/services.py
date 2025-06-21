import random
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from .models import PrizeWheelConfig, Prize, SpinAttempt

def get_prize_wheel_config():
    """Retorna a primeira (e idealmente única) instância de PrizeWheelConfig."""
    return PrizeWheelConfig.objects.first()

def can_user_spin(ip_address):
    """
    Verifica se o usuário (identificado pelo IP) pode girar a roda.
    Retorna True se puder, False caso contrário.
    """
    config = get_prize_wheel_config()
    if not config or not config.is_active:
        return False, "A Roda da Sorte está desativada."

    today_min = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_max = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    attempts_today = SpinAttempt.objects.filter(
        ip_address=ip_address,
        timestamp__range=(today_min, today_max)
    ).count()

    if attempts_today >= config.attempts_per_ip_daily:
        return False, f"Você atingiu o limite de {config.attempts_per_ip_daily} tentativas por dia."
    
    return True, "Você pode girar a roda!"

@transaction.atomic
def perform_spin(ip_address):
    """
    Processa uma tentativa de girar a roda para um determinado IP.
    Retorna um dicionário com: {'prize_won': Prize_instance_or_None, 'message': str, 'can_spin_again': bool}
    """
    can_spin, message = can_user_spin(ip_address)
    if not can_spin:
        # Recalcula can_spin_again para o caso de o limite ser atingido nesta tentativa
        # (embora a verificação inicial já devesse pegar isso)
        still_can_spin_today, _ = can_user_spin(ip_address) 
        return {'prize_won': None, 'message': message, 'can_spin_again': still_can_spin_today}

    config = get_prize_wheel_config() # Já sabemos que existe e está ativo
    won_prize_object = None
    
    # 1. Verificar a chance geral de ganhar algo
    # overall_win_chance é uma porcentagem, ex: 0.5 para 0.5%
    # random.uniform(0, 100) gera um float entre 0.0 e 100.0
    if random.uniform(0, 100) < float(config.overall_win_chance):
        # Usuário ganhou ALGO, agora sortear qual prémio
        active_prizes = Prize.objects.filter(is_active=True)
        
        # Filtrar prémios que ainda têm quantidade (ou quantidade ilimitada)
        available_prizes = [
            p for p in active_prizes 
            if p.quantity is None or p.quantity > 0
        ]
        
        if available_prizes:
            total_weight = sum(p.probability_weight for p in available_prizes)
            if total_weight > 0:
                chosen_weight = random.uniform(0, total_weight)
                current_weight = 0
                for prize in available_prizes:
                    current_weight += prize.probability_weight
                    if current_weight >= chosen_weight:
                        won_prize_object = prize
                        # Decrementar quantidade se finita
                        if won_prize_object.quantity is not None:
                            won_prize_object.quantity -= 1
                            won_prize_object.save(update_fields=['quantity'])
                        break
    
    # Registrar a tentativa
    spin_attempt_instance = SpinAttempt.objects.create(
        ip_address=ip_address,
        prize_won=won_prize_object
    )

    # Determinar mensagem e se pode girar novamente
    can_spin_again_after_this, _ = can_user_spin(ip_address)

    if won_prize_object:
        message = f"Parabéns! Você ganhou: {won_prize_object.name}!"
    else:
        message = "Que pena! Não foi desta vez. Tente novamente!"
        
    return {
        'prize_won': won_prize_object,
        'message': message,
        'can_spin_again': can_spin_again_after_this,
        'attempt_id': spin_attempt_instance.id if won_prize_object else None # Retorna o ID da tentativa se ganhou algo
    }
