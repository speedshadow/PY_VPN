from django.shortcuts import render
from .models_faq import FAQ

def faq_view(request):
    faqs = FAQ.objects.all()
    return render(request, 'blog/faq.html', {'faqs': faqs})
