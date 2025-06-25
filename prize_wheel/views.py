from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # To simplify, but ideally use CSRF
from .models import SpinAttempt
from .services import perform_spin, get_prize_wheel_config

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt # Remove or configure CSRF correctly for production
@require_POST # Only allow POST requests
def spin_the_wheel_api(request):
    ip_address = get_client_ip(request)
    config = get_prize_wheel_config()

    if not config or not config.is_active:
        return JsonResponse({'error': 'The Prize Wheel is disabled.', 'can_spin_again': False}, status=403)

    result = perform_spin(ip_address)
    
    prize_won_data = None
    attempt_id_for_email_submission = None
    if result['prize_won']:
        prize_won_data = {
            'id': result['prize_won'].id, # This is the prize ID, which the frontend needs
            'name': result['prize_won'].name,
            'description': result['prize_won'].description,
        }
        # We need the ID of the created SpinAttempt.
        # The perform_spin function already creates the SpinAttempt.
        # We will modify perform_spin to return the attempt_id.
        attempt_id_for_email_submission = result.get('attempt_id') # We will add this to the return of perform_spin

    return JsonResponse({
        'message': result['message'],
        'prize_won': prize_won_data,
        'can_spin_again': result['can_spin_again'],
        'attempt_id': attempt_id_for_email_submission # SpinAttempt ID for email submission
    })

# Optional: View to get initial wheel data for the frontend
# def prize_wheel_data_api(request):
#     config = get_prize_wheel_config()
#     if not config or not config.is_active:
#         return JsonResponse({'is_active': False, 'prizes': []})
#     
#     # If you use this view, uncomment the import of 'Prize' from .models
#     # from .models import Prize 
#     active_prizes = Prize.objects.filter(is_active=True)
#     prizes_data = [{
#         'id': p.id, 
#         'name': p.name, 
#         # 'image_url': p.image.url if p.image else None, # if we have prize images
#         # 'display_text': p.display_text # A field for custom text on the wheel
#     } for p in active_prizes]
#     
#     return JsonResponse({
#         'is_active': config.is_active,
#         'prizes': prizes_data,
#         # Other configs for the frontend, like colors, etc.
#     })

@csrf_exempt # Remove or configure CSRF correctly for production
@require_POST
def submit_winner_email_api(request, attempt_id):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'error': 'Email is required.'}, status=400)

    try:
        attempt = SpinAttempt.objects.get(id=attempt_id)
    except SpinAttempt.DoesNotExist:
        return JsonResponse({'error': 'Attempt not found.'}, status=404)

    if not attempt.prize_won:
        return JsonResponse({'error': 'This attempt did not result in a prize.'}, status=400)

    if attempt.winner_email:
        return JsonResponse({'error': 'Email already submitted for this attempt.'}, status=400)

    # Basic email validation (Django forms would do better, but for a simple API)
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Invalid email format.'}, status=400)

    attempt.winner_email = email
    attempt.save(update_fields=['winner_email'])

    return JsonResponse({'message': 'Email registered successfully!'})
