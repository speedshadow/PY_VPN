from django.shortcuts import render, get_object_or_404, redirect
from .models import BlogPost, Category, Comment
from .forms import CommentForm
from django.contrib import messages
from django.contrib.auth import get_user_model

def blog_public_list(request):
    featured_posts = BlogPost.objects.filter(published=True, featured=True).order_by('-created_at')
    recent_posts = BlogPost.objects.filter(published=True, featured=False).order_by('-created_at')

    # Calcula o tempo de leitura para cada post
    for post in featured_posts:
        post.read_time = estimate_read_time(post.content)
    for post in recent_posts:
        post.read_time = estimate_read_time(post.content)

    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts
    }
    return render(request, 'blog/blog_list_public.html', context)

def estimate_read_time(text, wpm=200):
    import re
    word_count = len(re.findall(r'\w+', text or ''))
    return max(1, int(word_count / wpm + 0.5))

def blog_public_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    
    # Get only top-level comments
    comments = post.comments.filter(approved=True, parent__isnull=True)
    comment_form = None

    if post.comments_enabled:
        if request.method == 'POST':
            comment_form = CommentForm(data=request.POST)
            if comment_form.is_valid():
                # Step 1: Create the comment object without the parent and save it.
                new_comment = Comment(
                    post=post,
                    author_name=comment_form.cleaned_data['author_name'],
                    author_email=comment_form.cleaned_data['author_email'],
                    content=comment_form.cleaned_data['content']
                )
                new_comment.save() # First save

                # Step 2: If there's a parent_id, assign it and save again.
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=int(parent_id))
                        new_comment.parent = parent_comment
                        new_comment.save() # Second save to persist the parent relationship
                    except (ValueError, Comment.DoesNotExist):
                        # If parent is invalid, the comment remains a top-level one.
                        pass
                
                messages.success(request, 'Your comment has been submitted and is awaiting approval.')
                return redirect('blog_public_detail', slug=post.slug)
        else:
            comment_form = CommentForm()

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
    read_time = estimate_read_time(post.content)

    liked = request.session.get(f'liked_post_{slug}', False)
    context = {
        'post': post,
        'related_posts': related_posts,
        'read_time': read_time,
        'request': request,
        'liked': liked,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'blog/blog_detail_public.html', context)

def blog_category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = BlogPost.objects.filter(category=category, published=True).order_by('-created_at')
    # Calcula o tempo de leitura para cada post
    for post in posts:
        post.read_time = estimate_read_time(post.content)
    return render(request, 'blog/blog_category_list.html', {'category': category, 'posts': posts})

from django.http import JsonResponse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def blog_like(request, slug):
    # Usa session para evitar múltiplos likes do mesmo usuário na mesma sessão
    session_key = f'liked_post_{slug}'
    if request.session.get(session_key, False):
        # Já curtiu nesta sessão, só retorna o valor atual
        post = get_object_or_404(BlogPost, slug=slug, published=True)
        return JsonResponse({"likes": post.likes})
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    BlogPost.objects.filter(pk=post.pk).update(likes=models.F('likes') + 1)
    post.refresh_from_db()
    request.session[session_key] = True
    return JsonResponse({"likes": post.likes})

