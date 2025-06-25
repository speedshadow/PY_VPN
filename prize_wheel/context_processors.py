from .models import Prize

def prize_wheel_prizes(request):
    active_prizes_qs = Prize.objects.filter(is_active=True, quantity__gt=0).order_by('name')
    # Converter QuerySet para uma lista de dicionários com os campos necessários para o JS
    prize_list_for_json = list(active_prizes_qs.values('id', 'name'))

    # Debugging lines para verificar os dados no console do servidor (opcional, pode descomentar se necessário)
    # print(f"DEBUG CONTEXT PROCESSOR: Raw QuerySet (representation): {list(active_prizes_qs)}")
    # print(f"DEBUG CONTEXT PROCESSOR: Prize list being sent to template (for JSON): {prize_list_for_json}")

    return {'prize_wheel_active_prizes': prize_list_for_json}
