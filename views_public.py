from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

@csrf_protect
def faq_view(request):
    return render(request, 'faq.html')

@csrf_protect
def contact_view(request):
    if request.method == 'POST':
        # Simples: apenas mostra mensagem de sucesso (não envia email real)
        messages.success(request, 'Your message has been sent!')
        return redirect('contact')
    return render(request, 'contact.html')
