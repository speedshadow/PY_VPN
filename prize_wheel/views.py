from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # Para simplificar, mas idealmente usar CSRF
from .models import SpinAttempt #, Prize # Descomente Prize se usar prize_wheel_data_api
from .services import perform_spin, get_prize_wheel_config

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt # Remover ou configurar CSRF corretamente para produção
@require_POST # Apenas permitir requisições POST
def spin_the_wheel_api(request):
    ip_address = get_client_ip(request)
    config = get_prize_wheel_config()

    if not config or not config.is_active:
        return JsonResponse({'error': 'A Roda da Sorte está desativada.', 'can_spin_again': False}, status=403)

    result = perform_spin(ip_address)
    
    prize_won_data = None
    attempt_id_for_email_submission = None
    if result['prize_won']:
        prize_won_data = {
            'id': result['prize_won'].id, # Este é o ID do prémio, que o frontend precisa
            'name': result['prize_won'].name,
            'description': result['prize_won'].description,
        }
        # Precisamos do ID da SpinAttempt que foi criada.
        # A função perform_spin já cria a SpinAttempt. Vamos assumir que ela retorna o objeto.
        # Se perform_spin não retorna o objeto SpinAttempt, precisaremos ajustá-la também.
        # Por agora, vamos assumir que result['spin_attempt_instance'] existe ou que podemos buscá-la.
        # Melhor ainda: perform_spin deveria retornar o ID da tentativa.
        # Vamos modificar perform_spin para retornar o attempt_id.
        attempt_id_for_email_submission = result.get('attempt_id') # Adicionaremos isso ao retorno de perform_spin

    return JsonResponse({
        'message': result['message'],
        'prize_won': prize_won_data,
        'can_spin_again': result['can_spin_again'],
        'attempt_id': attempt_id_for_email_submission # ID da SpinAttempt para submissão de email
    })

# Opcional: View para obter dados iniciais da roda para o frontend
# def prize_wheel_data_api(request):
#     config = get_prize_wheel_config()
#     if not config or not config.is_active:
#         return JsonResponse({'is_active': False, 'prizes': []})
#     
#     # Se for usar esta view, descomente a importação de 'Prize' de .models
#     # from .models import Prize 
#     active_prizes = Prize.objects.filter(is_active=True)
#     prizes_data = [{
#         'id': p.id, 
#         'name': p.name, 
#         # 'image_url': p.image.url if p.image else None, # Se tivermos imagens de prémios
#         # 'display_text': p.display_text # Um campo para texto customizado na roda
#     } for p in active_prizes]
#     
#     return JsonResponse({
#         'is_active': config.is_active,
#         'prizes': prizes_data,
#         # Outras configs para o frontend, como cores, etc.
#     })

@csrf_exempt # Remover ou configurar CSRF corretamente para produção
@require_POST
def submit_winner_email_api(request, attempt_id):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'error': 'Email é obrigatório.'}, status=400)

    try:
        attempt = SpinAttempt.objects.get(id=attempt_id)
    except SpinAttempt.DoesNotExist:
        return JsonResponse({'error': 'Tentativa não encontrada.'}, status=404)

    if not attempt.prize_won:
        return JsonResponse({'error': 'Esta tentativa não resultou num prémio.'}, status=400)

    if attempt.winner_email:
        return JsonResponse({'error': 'Email já submetido para esta tentativa.'}, status=400)

    # Validação básica de email (Django forms faria melhor, mas para API simples)
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'error': 'Formato de email inválido.'}, status=400)

    attempt.winner_email = email
    attempt.save(update_fields=['winner_email'])

    return JsonResponse({'message': 'Email registrado com sucesso!'})
