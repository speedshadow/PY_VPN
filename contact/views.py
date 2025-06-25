from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ContactMessage
from .forms import ContactForm

from django.http import JsonResponse
import json

def contact_view(request):
    if request.method == "POST":
        if request.headers.get('Content-Type') == 'application/json':
            data = json.loads(request.body)
            challenge_num1 = int(data.get('challenge_num1', 0))
            challenge_num2 = int(data.get('challenge_num2', 0))
            challenge_answer = int(data.get('challenge_answer', -1))
            if challenge_num1 + challenge_num2 != challenge_answer:
                return JsonResponse({'success': False, 'error': 'Anti-spam: resposta errada.'}, status=400)
            form = ContactForm(data)
        else:
            challenge_num1 = int(request.POST.get('challenge_num1', 0))
            challenge_num2 = int(request.POST.get('challenge_num2', 0))
            challenge_answer = int(request.POST.get('challenge_answer', -1))
            if challenge_num1 + challenge_num2 != challenge_answer:
                messages.error(request, 'Anti-spam: resposta errada.')
                return redirect("contact")
            form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': True})
            else:
                messages.success(request, "Message sent successfully!")
                return redirect("contact")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': form.errors.as_json()}, status=400)
    else:
        form = ContactForm()
    return render(request, "contact/contact.html", {"form": form})
