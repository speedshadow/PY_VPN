from django.utils.deprecation import MiddlewareMixin
import secrets
import base64

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Generate a new nonce for each request
        request.csp_nonce = base64.b64encode(secrets.token_bytes(32)).decode('utf-8')

    def process_response(self, request, response):
        if hasattr(request, 'csp_nonce'): # Ensure nonce was generated
            # Define uma política de segurança de conteúdo (CSP) robusta
            csp_policy = (
            "default-src 'self'; "
            f"script-src 'self' https://cdn.jsdelivr.net 'unsafe-eval' 'nonce-{request.csp_nonce}'; "
            "style-src 'self' https://fonts.googleapis.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

            response['Content-Security-Policy'] = ''.join(csp_policy.splitlines())
            response['X-Content-Type-Options'] = 'nosniff'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
