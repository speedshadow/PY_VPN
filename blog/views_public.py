from django.shortcuts import render, get_object_or_404
from .models import BlogPost

def blog_public_list(request):
    posts = BlogPost.objects.filter(published=True).order_by('-created_at')
    return render(request, 'blog/blog_list_public.html', {'posts': posts})

def blog_public_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, published=True)
    
    # Get related posts: 3 most recent published posts, excluding the current one
    related_posts = BlogPost.objects.filter(
        published=True
    ).exclude(
        id=post.id
    ).order_by('-created_at')[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts
    }
    return render(request, 'blog/blog_detail_public.html', context)
