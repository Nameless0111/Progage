from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.conf import settings
from .models import User, Profile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(max_length=30, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=20, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, required=True)
    avatar = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reCAPTCHA полностью отключена

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'avatar')

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'avatar', 'bio', 'phone')

class ProfileUpdateForm(forms.ModelForm):
    two_factor_enabled = forms.BooleanField(required=False, label='Включить двухфакторную аутентификацию')
    
    class Meta:
        model = Profile
        fields = ('preferences', 'two_factor_enabled')

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя или Email'
        self.fields['password'].label = 'Пароль'
        # reCAPTCHA удалена

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ваш email'}))

class TwoFactorForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'autofocus': True,
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric'
        }),
        label='Код из приложения',
        help_text='Введите 6-значный код из Google Authenticator'
    )
    
    backup_code = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ABCDEF12',
            'autocomplete': 'off'
        }),
        label='Резервный код',
        help_text='Если у вас нет доступа к приложению, используйте резервный код'
    )

class TwoFactorSetupForm(forms.Form):
    pass
