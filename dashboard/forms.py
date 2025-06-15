from django import forms
from vpn.models import VPN

class VPNForm(forms.ModelForm):
    devices_supported = forms.MultipleChoiceField(
        choices=VPN.DEVICE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Devices Supported'
    )
    # Override JSONField to accept free text, we will parse manually
    speeds_by_country = forms.CharField(
        widget=forms.Textarea(attrs={"rows":4, "class":"mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"}),
        required=False,
        label="Speeds by Country",
        help_text="One per line e.g. Germany: 300Mbps"
    )
    def clean_slug(self):
        data = self.cleaned_data.get('slug')
        # Se o usuário digitou 'slug' ou deixou igual para todos, limpa para forçar geração automática
        if data == 'slug':
            return ''
        return data

    def clean_devices_supported(self):
        data = self.cleaned_data.get('devices_supported')
        # Debug temporário para identificar erro
        # print('devices_supported:', repr(data), type(data))
        if isinstance(data, (list, tuple)):
            return [str(d) for d in data]
        if isinstance(data, str):
            return [data]
        return []
    def clean_speeds_by_country(self):
        data = self.cleaned_data.get('speeds_by_country')
        # Corrige bug: nunca passar lista para json.loads
        # Aceita dict direto
        if isinstance(data, dict):
            return data
        # Aceita vazio
        if not data:
            return {}
        # Aceita string do textarea: 'Germany: 300Mbps\nPortugal: 430Mbps'
        result = {}
        if isinstance(data, str):
            for line in data.splitlines():
                if ':' in line:
                    country, speed = line.split(':', 1)
                    result[country.strip()] = speed.strip()
            return result
        # Se vier lista (ex: [['Germany', '300Mbps'], ...] ou [{'country': 'Germany', 'speed': '300Mbps'}, ...])
        if isinstance(data, list):
            try:
                # Caso seja lista de pares
                if all(isinstance(i, (list, tuple)) and len(i) == 2 for i in data):
                    return {str(k): str(v) for k, v in data}
                # Caso seja lista de dicts
                if all(isinstance(i, dict) and 'country' in i and 'speed' in i for i in data):
                    return {str(i['country']): str(i['speed']) for i in data}
            except Exception as e:
                # print('DEBUG speeds_by_country LIST EXCEPTION:', str(e))
                return {}
            return {}
        # Log temporário para debug
        print('DEBUG speeds_by_country type:', type(data), 'value:', repr(data))
        # Se não for string nem dict nem lista, retorna dict vazio
        return {}

    class Meta:
        model = VPN
        fields = '__all__'
        help_texts = {
            'slug': 'Deixe em branco para gerar automaticamente pelo nome. Não use o valor "slug".'
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'logo': forms.URLInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'logo_upload': forms.ClearableFileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'}),
            'categories': forms.CheckboxSelectMultiple,
            
            'overall_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'security_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'privacy_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'speed_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'streaming_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'torrenting_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'additional_features_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'device_compatibility_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'server_locations_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'user_experience_rating': forms.NumberInput(attrs={'type': 'range', 'min': 0, 'max': 10, 'step': 1, 'class': 'w-full'}),
            'pros': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'One pro per line'}),
            'cons': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm', 'placeholder': 'One con per line'}),
            
            'based_country': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'num_servers': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'price': forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            'affiliate_link': forms.URLInput(attrs={'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'}),
            
        }
