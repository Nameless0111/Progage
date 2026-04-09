# #Security Demo Guide - Where to Find Protection Code

## #Overview
This document shows exactly where security protections are implemented in the Progage project. Use this guide to demonstrate security features in your code.

## #1. Two-Factor Authentication (2FA)

### #File: `accounts/models.py`
```python
# Lines 48-63: TOTP device management
def get_totp_device(self):
    """Get or create TOTP device"""
    device, created = TOTPDevice.objects.get_or_create(
        user=self.user,
        name='Progage 2FA',
        confirmed=True
    )
    return device

# Lines 48-63: Backup codes generation
def generate_backup_codes(self):
    """Generate backup codes"""
    import secrets
    codes = [secrets.token_hex(4).upper() for _ in range(10)]
    self.backup_codes = codes
    self.save()
    return codes
```

### #File: `accounts/views.py`
```python
# Lines 232-278: 2FA verification view
def two_factor_verify(request):
    """Verify two-factor code"""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('accounts:login')
    
    # Check TOTP code or backup code
    if code:
        device = profile.get_totp_device()
        if device.verify_token(code):
            # Success - login user
            login(request, user)
            return redirect('home')

# Lines 280-318: 2FA setup view
def two_factor_setup(request):
    """Setup two-factor authentication"""
    device = profile.get_totp_device()
    qr_code_url = device.config_url
    # Show QR code and backup codes
```

### #File: `accounts/forms.py`
```python
# Lines 48-73: TwoFactorForm
class TwoFactorForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=False,  # Allow either TOTP or backup code
        widget=forms.TextInput(attrs={
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        label='TOTP Code'
    )
    backup_code = forms.CharField(
        max_length=8,
        required=False,
        label='Backup Code'
    )
```

## #2. Brute Force Protection

### #File: `accounts/middleware.py`
```python
# Lines 6-66: Complete brute force protection
class BruteForceProtectionMiddleware(MiddlewareMixin):
    """Rate limiting for login attempts"""
    
    def __call__(self, request):
        # Apply only to login and password reset forms
        if request.path in ['/accounts/login/', '/accounts/password-reset/']:
            client_ip = self.get_client_ip(request)
            username = request.POST.get('username', '')
            
            if self.is_blocked(client_ip, username):
                return HttpResponse(
                    "Too many attempts. Try again in 5 minutes.",
                    status=429
                )
    
    def is_blocked(self, ip, username=''):
        # Block if >5 attempts per IP or >3 per username+IP
        ip_attempts = cache.get(f'login_attempts_ip_{ip}', 0)
        user_attempts = cache.get(f'login_attempts_user_{username}_{ip}', 0)
        return ip_attempts >= 5 or user_attempts >= 3
```

### #File: `accounts/views.py`
```python
# Lines 35-88: Login with rate limiting
def login_view(request):
    if request.method == 'POST':
        client_ip = get_client_ip(request)
        username = request.POST.get('username', '')
        
        if is_rate_limited(client_ip, username):
            return HttpResponse("Too many attempts.", status=429)
        
        # Check credentials...
        if user is not None:
            reset_login_attempts(client_ip, username)  # Reset on success
        else:
            record_failed_attempt(client_ip, username)  # Record failure
```

## #3. Comprehensive Logging & Audit

### #File: `adminpanel/middleware.py`
```python
# Lines 13-184: Complete logging middleware
class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Log every incoming request
        SystemLog.objects.create(
            level='INFO',
            message=f"[{request_type}] {request.method} {request.path}",
            user=request.user,
            ip_address=self._get_client_ip(request),
            extra_data={
                'request_id': request.request_id,
                'method': request.method,
                'path': request.path,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )
    
    def process_response(self, request, response):
        # Log responses and slow requests
        duration = (timezone.now() - request.start_time).total_seconds()
        if duration > 2.0:  # Log slow requests
            SystemLog.objects.create(
                level='WARNING',
                message=f"[SLOW_REQUEST] {request.method} {request.path} - {duration:.2f}s",
                user=request.user,
                extra_data={'duration': duration}
            )
    
    def process_exception(self, request, exception):
        # Log all exceptions
        ErrorLog.objects.create(
            error_type='EXCEPTION',
            message=str(exception),
            stack_trace=traceback.format_exc(),
            url=request.get_full_path(),
            user=request.user
        )
```

### #File: `adminpanel/models.py`
```python
# Lines 1-50: Activity logging models
class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    object_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    action_time = models.DateTimeField(auto_now_add=True)

class ErrorLog(models.Model):
    error_type = models.CharField(max_length=50)
    message = models.TextField()
    stack_trace = models.TextField()
    url = models.URLField()
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
```

## #4. Secure File Handling

### #File: `accounts/models.py`
```python
# Lines 29-46: Avatar URL with fallback
@property
def avatar_url(self):
    name = (self.get_full_name() or self.username or self.email or "User").strip()
    fallback = f"https://ui-avatars.com/api/?background=0D6EFD&color=fff&name={quote(name)}&size=128"
    
    if not self.avatar or not getattr(self.avatar, "name", None):
        return fallback
    
    try:
        if not self.avatar.storage.exists(self.avatar.name):
            return fallback
    except Exception:
        pass
    
    try:
        return self.avatar.url
    except Exception:
        return fallback
```

### #File: `courses/models.py`
```python
# Lines 47-63: Thumbnail URL with fallback
@property
def thumbnail_url(self):
    fallback = f"https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200&auto=format&fit=crop&q=60&sig={quote(self.title)}"
    
    if not self.thumbnail or not getattr(self.thumbnail, "name", None):
        return fallback
    
    try:
        if not self.thumbnail.storage.exists(self.thumbnail.name):
            return fallback
    except Exception:
        pass
    
    try:
        return self.thumbnail.url
    except Exception:
        return fallback
```

## #5. CSRF Protection

### #File: All Template Files
```html
<!-- Every form has CSRF token -->
<form method="post">
    {% csrf_token %}
    <!-- Form fields -->
</form>
```

Examples:
- `templates/accounts/login.html`
- `templates/accounts/register.html`
- `templates/courses/course_detail.html`
- `templates/chat/chat_detail.html`
- `templates/adminpanel/user_form.html`

## #6. Password Validation

### #File: `progage/settings.py`
```python
# Lines 139-152: Password validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## #7. Session Security

### #File: `progage/settings.py`
```python
# Lines 88-101: Security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware
    'accounts.middleware.BruteForceProtectionMiddleware',
    'adminpanel.middleware.LoggingMiddleware',
]
```

## #8. Database Security

### #File: `progage/settings.py`
```python
# Lines 131-133: Secure database configuration
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3')))
}
# Uses environment variables for credentials
```

## #9. Email Security

### #File: `progage/settings.py`
```python
# Lines 200-210: Secure email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # Secure TLS
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 60
DEFAULT_FROM_EMAIL = 'pashokbilashenko335@gmail.com'
```

## #10. API Security (REST Framework)

### #File: `progage/settings.py`
```python
# Lines 177-188: REST Framework security
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

## #How to Demo Each Protection

### #1. 2FA Demo
1. Go to user profile
2. Enable "Two-factor authentication"
3. Show QR code generation
4. Try login with TOTP code
5. Try backup code

### #2. Brute Force Demo
1. Try login with wrong password 6 times
2. Show "Too many attempts" message
3. Wait 5 minutes or change IP

### #3. Logging Demo
1. Check adminpanel -> Activity Logs
2. Show all user actions
3. Check Error Logs for exceptions
4. Show System Logs for requests

### #4. File Security Demo
1. Delete avatar file from media/avatars/
2. Show fallback avatar still works
3. Same for course thumbnails

### #5. CSRF Demo
1. Try to submit form without CSRF token
2. Show 403 Forbidden error

## #Security Checklist Summary

| Protection | File(s) | Status |
|-------------|---------|---------|
| 2FA | accounts/models.py, views.py, forms.py | #Active |
| Brute Force | accounts/middleware.py, views.py | #Active |
| Logging | adminpanel/middleware.py, models.py | #Active |
| File Security | accounts/models.py, courses/models.py | #Active |
| CSRF | All templates | #Active |
| Password Validation | progage/settings.py | #Active |
| Session Security | progage/settings.py | #Active |
| Database Security | progage/settings.py | #Active |
| Email Security | progage/settings.py | #Active |
| API Security | progage/settings.py | #Active |

## #What Was Cleaned Up

### #Removed Files:
- All temporary server scripts (debug_server.py, final_public.py, etc.)
- All deployment guides (DDOS_PROTECTION.md, README_DEPLOY.md, etc.)
- All diagram files (*.drawio)
- All test scripts (test_recaptcha.py, etc.)
- All migration scripts (migrate_to_mysql.py, etc.)

### #Kept Files:
- `SECURITY_CHECKLIST.md` - Complete security guide
- `SECURITY_DEMO_GUIDE.md` - This file
- Core application files
- Configuration files
- Production deployment files

## #Ready for Demo

Your project is now clean and ready for security demonstration. All protections are active and documented in this guide.
