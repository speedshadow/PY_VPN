from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import SiteSettings
from .forms import SiteSettingsForm

@login_required(login_url='/admin/login/')
def settings_edit(request):
    settings = SiteSettings.objects.first()
    if not settings:
        settings = SiteSettings.objects.create()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            settings = form.save()
            # Atualizar configurações do django-axes dinamicamente
            from django.conf import settings as dj_settings
            dj_settings.AXES_FAILURE_LIMIT = settings.axes_failure_limit
            dj_settings.AXES_COOLOFF_TIME = settings.axes_cooloff_time
            dj_settings.AXES_LOCK_OUT_AT_FAILURE = settings.axes_lock_out_at_failure
            dj_settings.AXES_USE_USER_AGENT = settings.axes_use_user_agent
            dj_settings.AXES_ONLY_USER_FAILURE = settings.axes_only_user_failure
            dj_settings.AXES_RESET_ON_SUCCESS = settings.axes_reset_on_success
            return redirect('settings:settings_edit')
        # Se o formulário não for válido, ele será renderizado abaixo com os erros
    else: # request.method == 'GET'
        form = SiteSettingsForm(instance=settings)
    
    # Para requisições GET ou POST com formulário inválido, renderiza o formulário
    return render(request, 'dashboard/settings_form.html', {'form': form})
