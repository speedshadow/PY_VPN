from django.shortcuts import render, get_object_or_404
from .models import BlogPost
from django.contrib.auth import get_user_model

def blog_public_list(request):
    featured_posts = BlogPost.objects.filter(published=True, featured=True).order_by('-created_at')
    posts = BlogPost.objects.filter(published=True).order_by('-created_at')
    return render(request, 'blog/blog_list_public.html', {'posts': posts, 'featured_posts': featured_posts})

def blog_public_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    # Incrementa views (ignora staff/admin e bots)
    if not request.user.is_staff and not request.user.is_superuser and not request.META.get('HTTP_USER_AGENT', '').lower().startswith('bot'):
        BlogPost.objects.filter(pk=post.pk).update(views=models.F('views') + 1)
        post.views += 1  # Reflete no template imediatamente

    # FIX: If post.author is a username string, replace it with the actual User object.
    if isinstance(getattr(post, 'author', None), str):
        User = get_user_model()
        try:
            author_obj = User.objects.get(username__iexact=post.author)
            post.author = author_obj  # Monkey-patch the post object for the template
        except User.DoesNotExist:
            # If user is not found, set author to None to prevent template errors.
            post.author = None

    related_posts = BlogPost.objects.filter(published=True).exclude(pk=post.pk).order_by('-created_at')[:3]

    context = {
        'post': post,
        'related_posts': related_posts,
        'request': request,
    }
    return render(request, 'blog/blog_detail_public.html', context)

from django.http import JsonResponse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def blog_like(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    BlogPost.objects.filter(pk=post.pk).update(likes=models.F('likes') + 1)
    post.refresh_from_db()
    return JsonResponse({"likes": post.likes})

