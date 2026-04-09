from django.conf import settings

def recaptcha_enabled(request):
    """Добавляет в контекст информацию о включенной reCAPTCHA"""
    return {
        'RECAPTCHA_ENABLED': (
            hasattr(settings, 'RECAPTCHA_PUBLIC_KEY') and 
            settings.RECAPTCHA_PUBLIC_KEY and 
            'test' not in settings.RECAPTCHA_PUBLIC_KEY
        )
    }
