import random
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone
from .models import PrizeWheelConfig, Prize, SpinAttempt

def get_prize_wheel_config():
    """Returns the first (and ideally only) instance of PrizeWheelConfig."""
    return PrizeWheelConfig.objects.first()

def can_user_spin(ip_address):
    """
    Checks if the user (identified by IP) can spin the wheel.
    Returns a tuple (can_spin: bool, message: str).
    """
    config = get_prize_wheel_config()
    if not config or not config.is_active:
        return False, "The Prize Wheel is disabled."

    today_min = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_max = timezone.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    
    attempts_today = SpinAttempt.objects.filter(
        ip_address=ip_address,
        timestamp__range=(today_min, today_max)
    ).count()

    if attempts_today >= config.attempts_per_ip_daily:
        return False, f"You have reached the limit of {config.attempts_per_ip_daily} attempts per day."
    
    return True, "You can spin the wheel!"

@transaction.atomic
def perform_spin(ip_address):
    """
    Processes a spin attempt for a given IP.
    Returns a dictionary with: {'prize_won': Prize_instance_or_None, 'message': str, 'can_spin_again': bool, 'attempt_id': int_or_None}
    """
    can_spin, message = can_user_spin(ip_address)
    if not can_spin:
        # Recalculate can_spin_again in case the limit is reached with this attempt
        # (although the initial check should already catch this)
        still_can_spin_today, _ = can_user_spin(ip_address) 
        return {'prize_won': None, 'message': message, 'can_spin_again': still_can_spin_today}

    config = get_prize_wheel_config() # We already know it exists and is active
    won_prize_object = None
    
    # 1. Check the overall chance of winning something
    # overall_win_chance is a percentage, e.g., 0.5 for 0.5%
    # random.uniform(0, 100) generates a float between 0.0 and 100.0
    if random.uniform(0, 100) < float(config.overall_win_chance):
        # User won SOMETHING, now draw for the prize
        active_prizes = Prize.objects.filter(is_active=True)
        
        # Filter prizes that still have quantity (or unlimited quantity)
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
                        # Decrement quantity if finite
                        if won_prize_object.quantity is not None:
                            won_prize_object.quantity -= 1
                            won_prize_object.save(update_fields=['quantity'])
                        break
    
    # Register the attempt
    spin_attempt_instance = SpinAttempt.objects.create(
        ip_address=ip_address,
        prize_won=won_prize_object
    )

    # Determine message and if they can spin again
    can_spin_again_after_this, _ = can_user_spin(ip_address)

    if won_prize_object:
        message = f"Congratulations! You won: {won_prize_object.name}!"
    else:
        message = "Too bad! Not this time. Try again!"
        
    return {
        'prize_won': won_prize_object,
        'message': message,
        'can_spin_again': can_spin_again_after_this,
        'attempt_id': spin_attempt_instance.id if won_prize_object else None # Return the attempt ID if something was won
    }
