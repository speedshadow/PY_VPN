from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CustomPage
from .forms import CustomPageForm
from django.http import Http404

@login_required(login_url='/admin/login/')
def custompage_list(request):
    pages = CustomPage.objects.all()
    return render(request, 'dashboard/custompage_list.html', {'pages': pages})

@login_required(login_url='/admin/login/')
def custompage_create(request):
    if request.method == 'POST':
        form = CustomPageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('custompage_list')
    else:
        form = CustomPageForm()
    return render(request, 'dashboard/custompage_form.html', {'form': form, 'page': None})

@login_required(login_url='/admin/login/')
def custompage_edit(request, pk):
    page = get_object_or_404(CustomPage, pk=pk)
    if request.method == 'POST':
        form = CustomPageForm(request.POST, instance=page)
        if form.is_valid():
            form.save()
            return redirect('custompage_list')
    else:
        form = CustomPageForm(instance=page)
    return render(request, 'dashboard/custompage_form.html', {'form': form, 'page': page})

@login_required(login_url='/admin/login/')
def custompage_delete(request, pk):
    page = get_object_or_404(CustomPage, pk=pk)
    if request.method == 'POST':
        page.delete()
        return redirect('custompage_list')
    return render(request, 'dashboard/custompage_confirm_delete.html', {'page': page})

def public_custompage(request, slug):
    page = get_object_or_404(CustomPage, slug=slug, is_active=True)
    return render(request, 'custompages/public_custompage.html', {'page': page})
