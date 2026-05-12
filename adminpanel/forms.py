from django import forms
from django.contrib.auth import get_user_model
from courses.models import Course

User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Оставьте пустым, чтобы не менять пароль'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле телефона из формы
        if 'phone' in self.fields:
            del self.fields['phone']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return username
            
        # Проверяем только при создании нового пользователя
        if not self.instance.pk:
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError('Пользователь с таким именем уже существует.')
        else:
            # При редактировании проверяем, что username не занят другим пользователем
            if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Пользователь с таким именем уже существует.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            return email
            
        # Проверяем только при создании нового пользователя
        if not self.instance.pk:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('Пользователь с таким email уже существует.')
        else:
            # При редактировании проверяем, что email не занят другим пользователем
            if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'date_of_birth', 'avatar', 'bio', 'is_active', 'role'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Логин',
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'date_of_birth': 'Дата рождения',
            'avatar': 'Аватар',
            'bio': 'О себе',
            'is_active': 'Активный пользователь',
            'role': 'Роль',
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'instructor', 'category', 'level', 'price',
            'thumbnail', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'instructor': 'Преподаватель',
            'category': 'Категория',
            'level': 'Уровень сложности',
            'price': 'Цена (₽)',
            'thumbnail': 'Превью',
            'is_published': 'Опубликован',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничить выбор преподавателей только авторами
        self.fields['instructor'].queryset = User.objects.filter(role='teacher')
