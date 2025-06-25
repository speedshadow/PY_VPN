# context_processors.py
# Adiciona STATIC_VERSION (timestamp) ao contexto para cache busting
import time

def static_version(request):
    return {
        'STATIC_VERSION': int(time.time())
    }
