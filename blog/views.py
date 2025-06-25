from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BlogPost
from .forms import BlogPostForm

@login_required(login_url='/admin/login/')
def blogpost_list(request):
    posts = BlogPost.objects.all()
    return render(request, 'dashboard/blogpost_list.html', {'posts': posts})

@login_required(login_url='/admin/login/')
def blogpost_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('blogpost_list')
    else:
        form = BlogPostForm()
    return render(request, 'dashboard/blogpost_form.html', {'form': form, 'post': None})

@login_required(login_url='/admin/login/')
def blogpost_edit(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blogpost_list')
    else:
        form = BlogPostForm(instance=post)
    return render(request, 'dashboard/blogpost_form.html', {'form': form, 'post': post})

@login_required(login_url='/admin/login/')
def blogpost_delete(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blogpost_list')
    return render(request, 'dashboard/blogpost_confirm_delete.html', {'post': post})
