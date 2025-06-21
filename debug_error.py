import sys
import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Import the view function that's causing the error
from blog.views_public import blog_public_detail
from django.test import RequestFactory
from django.template import Template, Context
from django.template.loader import get_template
from django.urls import reverse

# Create a fake request
factory = RequestFactory()
request = factory.get('/blog/what-best-vpns-2025/')
request.META['SERVER_NAME'] = 'localhost'
request.META['SERVER_PORT'] = '8080'

# Add the request to ALLOWED_HOSTS for testing
settings.ALLOWED_HOSTS.append('testserver')
settings.ALLOWED_HOSTS.append('localhost')

# Enable debug mode
settings.DEBUG = True

# Try loading the template directly
try:
    print("Tentando carregar o template diretamente...")
    template = get_template('blog/blog_detail_public.html')
    print("Template carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar o template: {type(e).__name__}")
    print(f"Mensagem de erro: {str(e)}")
    import traceback
    traceback.print_exc()

# Try to execute the view function
try:
    print("\nTentando executar a view blog_public_detail...")
    # Get the blog post slug from the URL
    slug = 'what-best-vpns-2025'
    response = blog_public_detail(request, slug)
    print("View executada com sucesso")
    print(f"Status code da resposta: {response.status_code}")
except Exception as e:
    print(f"Erro na view: {type(e).__name__}")
    print(f"Mensagem de erro: {str(e)}")
    import traceback
    traceback.print_exc()

# Try to identify specific template errors
try:
    print("\nVerificando possíveis erros no template...")
    from blog.models import BlogPost
    post = BlogPost.objects.filter(slug='what-best-vpns-2025', published=True).first()
    if post:
        print(f"Post encontrado: {post.title}")
        context = {
            'post': post,
            'related_posts': BlogPost.objects.filter(published=True).exclude(id=post.id)[:3],
            'request': request
        }
        # Try to render the template with the context
        template = get_template('blog/blog_detail_public.html')
        content = template.render(context)
        print("Template renderizado com sucesso!")
    else:
        print("Post não encontrado!")
except Exception as e:
    print(f"Erro ao renderizar o template: {type(e).__name__}")
    print(f"Mensagem de erro: {str(e)}")
    import traceback
    traceback.print_exc()
