import os
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import hashlib
import mimetypes
from .models_customization import (
    SiteCustomization, CustomCSS, CustomJavaScript #, SocialMediaLink, 
    #ContactInformation, ThemeColor, Typography, LayoutSettings
)
from .forms_customization import (
    SiteCustomizationForm, CustomCSSForm, CustomJavaScriptForm #, SocialMediaLinkForm, 
    #ContactInformationForm, ThemeColorForm, TypographyForm, LayoutSettingsForm, 
    # LogoUploadForm, FaviconUploadForm, # These forms do not exist here
    # FontUploadForm, ImageUploadForm # These forms do not exist here
)

logger = logging.getLogger(__name__)

# Helpers

def handle_uploaded_file(file, subfolder='uploads'):
    """
    Salva um arquivo enviado e retorna o caminho relativo
    """
    if not file:
        return None
        
    # Gera um nome de arquivo único
    file_ext = os.path.splitext(file.name)[1].lower()
    file_hash = hashlib.md5(file.read()).hexdigest()
    file.seek(0)  # Volta para o início do arquivo
    
    # Cria o caminho do arquivo
    filename = f"{file_hash}{file_ext}"
    filepath = os.path.join(subfolder, filename)
    
    # Salva o arquivo
    fs = default_storage
    if fs.exists(filepath):
        return filepath  # Já existe, retorna o caminho
    
    # Processa imagens para otimização
    if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
        try:
            # Abre a imagem
            img = Image.open(file)
            
            # Converte para RGB se for PNG com canal alpha
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            # Redimensiona se for muito grande (máx 2000px no maior lado)
            max_size = 2000
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Salva otimizada
            output = BytesIO()
            if file_ext.lower() in ['.jpg', '.jpeg']:
                img.save(output, format='JPEG', quality=85, optimize=True)
            elif file_ext.lower() == '.png':
                img.save(output, format='PNG', optimize=True)
            elif file_ext.lower() == '.webp':
                img.save(output, format='WEBP', quality=85, method=6)
            else:
                # Para outros formatos, salva como está
                output = file
            
            # Salva no armazenamento
            if hasattr(output, 'seek'):
                output.seek(0)
            fs.save(filepath, ContentFile(output.read()))
            return filepath
            
        except (UnidentifiedImageError, Exception) as e:
            logger.error(f"Erro ao processar imagem: {e}")
            # Se falhar, salva o arquivo original
            fs.save(filepath, file)
            return filepath
    else:
        # Para arquivos que não são imagens
        fs.save(filepath, file)
        return filepath

def get_custom_css():
    """Retorna todo o CSS personalizado ativo"""
    return '\n'.join(
        css.content for css in CustomCSS.objects.filter(is_active=True)
    )

def get_custom_js():
    """Retorna todo o JavaScript personalizado ativo"""
    return '\n'.join(
        js.script for js in CustomJavaScript.objects.filter(is_active=True)
    )

# def get_social_media_links():
#     """Retorna os links para mídias sociais"""
#     # return SocialMediaLink.objects.filter(is_active=True).order_by('order')
#     return []

# def get_theme_colors():
#     """Retorna as cores do tema"""
#     # theme_colors = {}
#     # for color in ThemeColor.objects.all():
#     #     theme_colors[color.name] = color.value
#     # return theme_colors
#     return {}

# Views

@login_required
@permission_required('settings.view_sitecustomization')
def customization_dashboard(request):
    """Painel de personalização do site"""
    site_customization = SiteCustomization.objects.first()
    custom_css = CustomCSS.objects.filter(is_active=True).count()
    custom_js = CustomJavaScript.objects.filter(is_active=True).count()
    # social_links = SocialMediaLink.objects.filter(is_active=True).count() # Commented out
    social_links_count = 0 # Placeholder for now

    # Verifica se há personalizações pendentes
    pending_changes = False
    if not site_customization:
        pending_changes = True

    context = {
        'site_customization': site_customization,
        'custom_css_count': custom_css,
        'custom_js_count': custom_js,
        'social_links_count': social_links_count, # Use placeholder
        'pending_changes': pending_changes,
        'title': 'Personalização do Site',
        'active_tab': 'dashboard',
    }
    return render(request, 'dashboard/customization/dashboard.html', context)

@login_required
@permission_required('settings.change_sitecustomization')
def customization_edit(request):
    """Edita as configurações gerais de personalização"""
    site_customization = SiteCustomization.objects.first()
    
    if request.method == 'POST':
        form = SiteCustomizationForm(
            request.POST, 
            request.FILES, 
            instance=site_customization
        )
        
        if form.is_valid():
            # Processa o upload do logo
            logo_file = request.FILES.get('logo')
            if logo_file:
                logo_path = handle_uploaded_file(logo_file, 'customization/logos')
                if logo_path:
                    form.instance.logo = logo_path
            
            # Processa o upload do favicon
            favicon_file = request.FILES.get('favicon')
            if favicon_file:
                favicon_path = handle_uploaded_file(favicon_file, 'customization/favicons')
                if favicon_path:
                    form.instance.favicon = favicon_path
            
            form.save()
            messages.success(request, 'Personalizações salvas com sucesso!')
            return redirect('customization_dashboard')
    else:
        form = SiteCustomizationForm(instance=site_customization)
    
    return render(request, 'dashboard/customization/settings.html', {
        'form': form,
        'site_customization': site_customization,
        'title': 'Configurações de Personalização',
        'active_tab': 'general',
    })

# @login_required
# @permission_required('settings.view_themecolor')
# def theme_colors(request):
#     """Gerencia as cores do tema"""
#     colors = ThemeColor.objects.all().order_by('name')
#     
#     if request.method == 'POST':
#         # Processa o formulário de cores
#         for color in colors:
#             color_name = f"color_{color.name}"
#             if color_name in request.POST:
#                 color.value = request.POST[color_name]
#                 color.save()
#         
#         messages.success(request, 'Cores do tema atualizadas com sucesso!')
#         return redirect('theme_colors')
#     
#     return render(request, 'dashboard/customization/theme_colors.html', {
#         'colors': [], # colors,
#         'title': 'Cores do Tema',
#         'active_tab': 'theme',
#     })

# @login_required
# @permission_required('settings.change_typography')
# def typography_settings(request):
#     """Configurações de tipografia"""
#     # typography = Typography.objects.first()
#     # 
#     # if not typography:
#     #     typography = Typography.objects.create()
#     # 
#     # if request.method == 'POST':
#     #     form = TypographyForm(request.POST, instance=typography)
#     #     
#     #     # Processa o upload de fonte personalizada
#     #     if 'font_file' in request.FILES:
#     #         font_form = FontUploadForm(request.POST, request.FILES)
#     #         if font_form.is_valid():
#     #             font_file = request.FILES['font_file']
#     #             font_name = font_form.cleaned_data['font_name']
#     #             
#     #             if font_file and font_name:
#     #                 # Salva o arquivo da fonte
#     #                 font_path = handle_uploaded_file(
#     #                     font_file, 
#     #                     'customization/fonts'
#     #                 )
#     #                 
#     #                 if font_path:
#     #                     # Adiciona a fonte à lista de fontes personalizadas
#     #                     custom_fonts = typography.custom_fonts or {}
#     #                     font_format = font_file.name.split('.')[-1].lower()
#     #                     
#     #                     custom_fonts[font_name] = {
#     #                         'path': font_path,
#     #                         'format': font_format,
#     #                         'added': timezone.now().isoformat()
#     #                     }
#     #                     
#     #                     typography.custom_fonts = custom_fonts
#     #                     typography.save()
#     #                     
#     #                     messages.success(request, 'Fonte personalizada adicionada com sucesso!')
#     #                     return redirect('typography_settings')
#     #     else:
#     #         if form.is_valid():
#     #             form.save()
#     #             messages.success(request, 'Configurações de tipografia salvas com sucesso!')
#     #             return redirect('typography_settings')
#     # else:
#     #     form = TypographyForm(instance=typography)
#     # 
#     # font_form = FontUploadForm()
#     # 
#     # return render(request, 'dashboard/customization/typography.html', {
#     #     'form': None, # form,
#     #     'font_form': None, # font_form,
#     #     'typography': None, # typography,
#     #     'title': 'Tipografia',
#     #     'active_tab': 'typography',
#     # })
#     pass

# @login_required
# @permission_required('settings.change_layoutsettings')
# def layout_settings(request):
#     """Configurações de layout"""
#     # layout = LayoutSettings.objects.first()
#     # 
#     # if not layout:
#     #     layout = LayoutSettings.objects.create()
#     # 
#     # if request.method == 'POST':
#     #     form = LayoutSettingsForm(request.POST, request.FILES, instance=layout)
#     #     
#     #     # Processa o upload de imagens de fundo
#     #     if 'background_image' in request.FILES:
#     #         bg_image = request.FILES['background_image']
#     #         if bg_image:
#     #             bg_path = handle_uploaded_file(bg_image, 'customization/backgrounds')
#     #             if bg_path:
#     #                 layout.background_image = bg_path
#     #     
#     #     if form.is_valid():
#     #         form.save()
#     #         messages.success(request, 'Configurações de layout salvas com sucesso!')
#     #         return redirect('layout_settings')
#     # else:
#     #     form = LayoutSettingsForm(instance=layout)
#     # 
#     # return render(request, 'dashboard/customization/layout.html', {
#     #     'form': None, # form,
#     #     'layout': None, # layout,
#     #     'title': 'Layout',
#     #     'active_tab': 'layout',
#     # })
#     pass

# @login_required
# @permission_required('settings.view_socialmedialink')
# def social_media_links(request):
#     """Gerencia os links de mídia social"""
#     # links = SocialMediaLink.objects.all().order_by('order')
#     # 
#     # if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#     #     # Atualiza a ordem dos itens via AJAX
#     #     try:
#     #         order_data = json.loads(request.body)
#     #         for item in order_data.get('order', []):
#     #             link = SocialMediaLink.objects.get(id=item['id'])
#     #             link.order = item['order']
#     #             link.save()
#     #         return JsonResponse({'status': 'success'})
#     #     except Exception as e:
#     #         return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
#     # 
#     # return render(request, 'dashboard/customization/social_media_links.html', {
#     #     'links': [], # links,
#     #     'title': 'Redes Sociais',
#     #     'active_tab': 'social',
#     # })
#     pass

# @login_required
# @permission_required('settings.add_socialmedialink')
# def social_media_link_add(request):
#     """Adiciona um novo link de mídia social"""
#     # if request.method == 'POST':
#     #     form = SocialMediaLinkForm(request.POST, request.FILES)
#     #     
#     #     # Processa o upload do ícone
#     #     if 'custom_icon' in request.FILES:
#     #         icon_file = request.FILES['custom_icon']
#     #         if icon_file:
#     #             icon_path = handle_uploaded_file(icon_file, 'customization/social_icons')
#     #             if icon_path:
#     #                 form.instance.custom_icon = icon_path
#     #     
#     #     if form.is_valid():
#     #         form.save()
#     #         messages.success(request, 'Link de mídia social adicionado com sucesso!')
#     #         return redirect('social_media_links')
#     # else:
#     #     form = SocialMediaLinkForm()
#     # 
#     # return render(request, 'dashboard/customization/social_media_link_form.html', {
#     #     'form': None, # form,
#     #     'title': 'Adicionar Rede Social',
#     #     'active_tab': 'social',
#     # })
#     pass

# @login_required
# @permission_required('settings.change_socialmedialink')
# def social_media_link_edit(request, pk):
#     """Edita um link de mídia social"""
#     # link = get_object_or_404(SocialMediaLink, pk=pk)
#     # 
#     # if request.method == 'POST':
#     #     form = SocialMediaLinkForm(request.POST, request.FILES, instance=link)
#     #     
#     #     # Processa o upload do ícone
#     #     if 'custom_icon' in request.FILES:
#     #         icon_file = request.FILES['custom_icon']
#     #         if icon_file:
#     #             icon_path = handle_uploaded_file(icon_file, 'customization/social_icons')
#     #             if icon_path:
#     #                 form.instance.custom_icon = icon_path
#     #     
#     #     if form.is_valid():
#     #         form.save()
#     #         messages.success(request, 'Link de mídia social atualizado com sucesso!')
#     #         return redirect('social_media_links')
#     # else:
#     #     form = SocialMediaLinkForm(instance=link)
#     # 
#     # return render(request, 'dashboard/customization/social_media_link_form.html', {
#     #     'form': None, # form,
#     #     'link': None, # link,
#     #     'title': 'Editar Rede Social',
#     #     'active_tab': 'social',
#     # })
#     pass

# @login_required
# @permission_required('settings.delete_socialmedialink')
# def social_media_link_delete(request, pk):
#     """Remove um link de mídia social"""
#     # link = get_object_or_404(SocialMediaLink, pk=pk)
#     # 
#     # if request.method == 'POST':
#     #     link.delete()
#     #     messages.success(request, 'Link de mídia social removido com sucesso!')
#     #     return redirect('social_media_links')
#     # 
#     # return render(request, 'dashboard/customization/confirm_delete.html', {
#     #     'object': None, # link,
#     #     'title': 'Confirmar Exclusão de Rede Social',
#     #     'active_tab': 'social',
#     # })
#     pass

# @login_required
# @permission_required('settings.view_contactinformation')
# def contact_information(request):
#     """Gerencia as informações de contato"""
#     # contact_info = ContactInformation.objects.first()
#     # 
#     # if not contact_info:
#     #     contact_info = ContactInformation.objects.create()
#     # 
#     # if request.method == 'POST':
#     #     form = ContactInformationForm(request.POST, instance=contact_info)
#     #     
#     #     if form.is_valid():
#     #         form.save()
#     #         messages.success(request, 'Informações de contato salvas com sucesso!')
#     #         return redirect('contact_information')
#     # else:
#     #     form = ContactInformationForm(instance=contact_info)
#     # 
#     # return render(request, 'dashboard/customization/contact_information.html', {
#     #     'form': None, # form,
#     #     'contact_info': None, # contact_info,
#     #     'title': 'Informações de Contato',
#     #     'active_tab': 'contact',
#     # })
#     pass

@login_required
@permission_required('settings.view_customcss')
def custom_css_list(request):
    """Lista os arquivos CSS personalizados"""
    css_files = CustomCSS.objects.all().order_by('name')
    
    return render(request, 'dashboard/customization/css_list.html', {
        'css_files': css_files,
        'title': 'CSS Personalizado',
        'active_tab': 'css',
    })

@login_required
@permission_required('settings.add_customcss')
def custom_css_add(request):
    """Adiciona um novo arquivo CSS personalizado"""
    if request.method == 'POST':
        form = CustomCSSForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Arquivo CSS adicionado com sucesso!')
            return redirect('custom_css_list')
    else:
        form = CustomCSSForm()
    
    return render(request, 'dashboard/customization/css_form.html', {
        'form': form,
        'title': 'Adicionar CSS Personalizado',
        'active_tab': 'css',
    })

@login_required
@permission_required('settings.change_customcss')
def custom_css_edit(request, pk):
    """Edita um arquivo CSS personalizado"""
    css_file = get_object_or_404(CustomCSS, pk=pk)
    
    if request.method == 'POST':
        form = CustomCSSForm(request.POST, instance=css_file)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Arquivo CSS atualizado com sucesso!')
            return redirect('custom_css_list')
    else:
        form = CustomCSSForm(instance=css_file)
    
    return render(request, 'dashboard/customization/css_form.html', {
        'form': form,
        'css_file': css_file,
        'title': 'Editar CSS Personalizado',
        'active_tab': 'css',
    })

@login_required
@permission_required('settings.delete_customcss')
def custom_css_delete(request, pk):
    """Remove um arquivo CSS personalizado"""
    css_file = get_object_or_404(CustomCSS, pk=pk)
    
    if request.method == 'POST':
        css_file.delete()
        messages.success(request, 'Arquivo CSS removido com sucesso!')
        return redirect('custom_css_list')
    
    return render(request, 'dashboard/customization/confirm_delete.html', {
        'object': css_file,
        'title': 'Confirmar Exclusão de CSS',
        'active_tab': 'css',
    })

@login_required
@permission_required('settings.view_customjs')
def custom_js_list(request):
    """Lista os arquivos JavaScript personalizados"""
    js_files = CustomJS.objects.all().order_by('name')
    
    return render(request, 'dashboard/customization/js_list.html', {
        'js_files': js_files,
        'title': 'JavaScript Personalizado',
        'active_tab': 'js',
    })

@login_required
@permission_required('settings.add_customjs')
def custom_js_add(request):
    """Adiciona um novo arquivo JavaScript personalizado"""
    if request.method == 'POST':
        form = CustomJSForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Arquivo JavaScript adicionado com sucesso!')
            return redirect('custom_js_list')
    else:
        form = CustomJSForm()
    
    return render(request, 'dashboard/customization/js_form.html', {
        'form': form,
        'title': 'Adicionar JavaScript Personalizado',
        'active_tab': 'js',
    })

@login_required
@permission_required('settings.change_customjs')
def custom_js_edit(request, pk):
    """Edita um arquivo JavaScript personalizado"""
    js_file = get_object_or_404(CustomJS, pk=pk)
    
    if request.method == 'POST':
        form = CustomJSForm(request.POST, instance=js_file)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Arquivo JavaScript atualizado com sucesso!')
            return redirect('custom_js_list')
    else:
        form = CustomJSForm(instance=js_file)
    
    return render(request, 'dashboard/customization/js_form.html', {
        'form': form,
        'js_file': js_file,
        'title': 'Editar JavaScript Personalizado',
        'active_tab': 'js',
    })

@login_required
@permission_required('settings.delete_customjs')
def custom_js_delete(request, pk):
    """Remove um arquivo JavaScript personalizado"""
    js_file = get_object_or_404(CustomJS, pk=pk)
    
    if request.method == 'POST':
        js_file.delete()
        messages.success(request, 'Arquivo JavaScript removido com sucesso!')
        return redirect('custom_js_list')
    
    return render(request, 'dashboard/customization/confirm_delete.html', {
        'object': js_file,
        'title': 'Confirmar Exclusão de JavaScript',
        'active_tab': 'js',
    })

@login_required
@permission_required('settings.change_sitecustomization')
def upload_logo(request):
    """Faz upload de um novo logo"""
    if request.method == 'POST' and request.FILES.get('logo'):
        form = LogoUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            logo_file = request.FILES['logo']
            logo_path = handle_uploaded_file(logo_file, 'customization/logos')
            
            if logo_path:
                # Atualiza ou cria o registro de personalização
                customization, created = SiteCustomization.objects.get_or_create()
                customization.logo = logo_path
                customization.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'url': customization.logo.url if customization.logo else ''
                    })
                
                messages.success(request, 'Logo atualizado com sucesso!')
                return redirect('customization_edit')
    else:
        form = LogoUploadForm()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao fazer upload do logo.'
        }, status=400)
    
    return redirect('customization_edit')

@login_required
@permission_required('settings.change_sitecustomization')
def upload_favicon(request):
    """Faz upload de um novo favicon"""
    if request.method == 'POST' and request.FILES.get('favicon'):
        form = FaviconUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            favicon_file = request.FILES['favicon']
            favicon_path = handle_uploaded_file(favicon_file, 'customization/favicons')
            
            if favicon_path:
                # Atualiza ou cria o registro de personalização
                customization, created = SiteCustomization.objects.get_or_create()
                customization.favicon = favicon_path
                customization.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'url': customization.favicon.url if customization.favicon else ''
                    })
                
                messages.success(request, 'Favicon atualizado com sucesso!')
                return redirect('customization_edit')
    else:
        form = FaviconUploadForm()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao fazer upload do favicon.'
        }, status=400)
    
    return redirect('customization_edit')

@login_required
@permission_required('settings.change_sitecustomization')
def upload_image(request):
    """Faz upload de uma imagem genérica"""
    if request.method == 'POST' and request.FILES.get('image'):
        form = ImageUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            image_file = request.FILES['image']
            subfolder = form.cleaned_data.get('subfolder', 'uploads')
            image_path = handle_uploaded_file(image_file, f'customization/{subfolder}')
            
            if image_path:
                image_url = default_storage.url(image_path)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'url': image_url,
                        'path': image_path
                    })
                
                return JsonResponse({
                    'location': image_url
                })
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Erro ao fazer upload da imagem.'
        }, status=400)
    
    return JsonResponse({'error': 'Método não permitido'}, status=405)

# API Views

@csrf_exempt
@require_http_methods(["POST"])
def api_save_customization(request):
    """API para salvar personalizações via AJAX"""
    try:
        data = json.loads(request.body)
        customization_type = data.get('type')
        
        if not customization_type:
            return JsonResponse(
                {'status': 'error', 'message': 'Tipo de personalização não especificado'}, 
                status=400
            )
        
        if customization_type == 'colors':
            # Atualiza as cores do tema
            for color_name, color_value in data.get('colors', {}).items():
                color, created = ThemeColor.objects.get_or_create(name=color_name)
                color.value = color_value
                color.save()
            
            return JsonResponse({'status': 'success'})
            
        elif customization_type == 'typography':
            # Atualiza a tipografia
            typography = Typography.objects.first()
            if not typography:
                typography = Typography.objects.create()
            
            # Atualiza os campos de tipografia
            for field in ['font_family', 'base_font_size', 'line_height', 'heading_font', 'heading_weight']:
                if field in data:
                    setattr(typography, field, data[field])
            
            typography.save()
            return JsonResponse({'status': 'success'})
            
        else:
            return JsonResponse(
                {'status': 'error', 'message': 'Tipo de personalização inválido'}, 
                status=400
            )
    
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': 'Dados inválidos'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Erro ao salvar personalização: {e}", exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': str(e)}, 
            status=500
        )

# Public Views

def custom_css(request):
    """Retorna o CSS personalizado como um arquivo CSS"""
    css_content = get_custom_css()
    response = HttpResponse(css_content, content_type='text/css')
    response['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 ano
    return response

def custom_js(request):
    """Retorna o JavaScript personalizado como um arquivo JS"""
    js_content = get_custom_js()
    response = HttpResponse(js_content, content_type='application/javascript')
    response['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 ano
    return response

def theme_css(request):
    """Retorna as variáveis de tema como CSS"""
    theme_colors = get_theme_colors()
    css_vars = [":root {"]
    
    for name, value in theme_colors.items():
        css_vars.append(f"  --color-{name}: {value};")
    
    # Adiciona outras variáveis de tema (tipografia, espaçamentos, etc.)
    typography = Typography.objects.first()
    if typography:
        css_vars.append(f"  --font-family: {typography.font_family or 'sans-serif'};")
        css_vars.append(f"  --font-size-base: {typography.base_font_size or '16px'};")
        css_vars.append(f"  --line-height: {typography.line_height or 1.5};")
        css_vars.append(f"  --heading-font: {typography.heading_font or 'inherit'};")
        css_vars.append(f"  --heading-weight: {typography.heading_weight or 'bold'};")
    
    css_vars.append("}")
    
    response = HttpResponse('\n'.join(css_vars), content_type='text/css')
    response['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 ano
    return response
