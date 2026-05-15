from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django.conf import settings
from .models import User, Profile, TeacherRating

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
    anonymous_mode = forms.BooleanField(
        required=False,
        label='Показывать меня как анонимного пользователя'
    )
    show_in_teachers_list = forms.BooleanField(
        required=False,
        initial=True,
        label='Показываться на странице преподавателей'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # reCAPTCHA полностью отключена

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'avatar')

class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(required=False, label='Имя пользователя')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'avatar')

class ProfileUpdateForm(forms.ModelForm):
    two_factor_enabled = forms.BooleanField(required=False, label='Включить двухфакторную аутентификацию')
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False, label='О себе')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    preferences = forms.JSONField(required=False, label='Настройки')
    
    class Meta:
        model = Profile
        fields = ('preferences', 'two_factor_enabled', 'bio', 'phone')

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Имя пользователя или Email'
        self.fields['password'].label = 'Пароль'
        # reCAPTCHA удалена

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Если введен email, оставляем как есть
            if '@' in username:
                return username.lower()
            # Если введен username, ищем пользователя и возвращаем его email
            else:
                try:
                    user = User.objects.get(username__iexact=username)
                    return user.email
                except User.DoesNotExist:
                    # Если пользователь не найден, возвращаем как есть для обработки ошибки
                    return username
        return username

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

class TeacherRatingForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=TeacherRating.RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ваша оценка'
    )
    
    class Meta:
        model = TeacherRating
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Расскажите о вашем опыте обучения с этим преподавателем...'})
        }
        labels = {
            'comment': 'Комментарий (необязательно)'
        }
