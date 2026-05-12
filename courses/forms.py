from django import forms
from .models import CourseReview, Course, Lesson, Category, TestQuestion, TestAnswer, PracticeAssignment, SecurityConfig, CodeSubmission


class CourseReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f'{i} ⭐') for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'rating-input'}),
        label='Рейтинг'
    )
    
    class Meta:
        model = CourseReview
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваш отзыв о курсе...'
            }),
        }
        labels = {
            'comment': 'Комментарий',
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category', 'level', 'programming_language', 'price', 'thumbnail', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'programming_language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Python, JavaScript, C++'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = "Выберите категорию"


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content', 'attachment', 'order', 'is_free']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'lesson_type': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Введите содержание лекции...'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'content': 'Содержание лекции',
            'attachment': 'Прикрепленный файл (видео, презентация, PDF, Word и др.)',
        }
        help_texts = {
            'content': 'Добавьте текстовое содержание лекции. Можно использовать HTML-теги для форматирования.',
            'attachment': 'Загрузите файл с материалами лекции: видео, презентация, PDF документ, Word файл и т.д.',
        }


class TestQuestionForm(forms.ModelForm):
    class Meta:
        model = TestQuestion
        fields = ['question_text', 'question_type', 'points', 'explanation', 'is_required']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите текст вопроса...'}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Необязательное пояснение к правильному ответу...'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'question_text': 'Текст вопроса',
            'question_type': 'Тип вопроса',
            'points': 'Баллы за вопрос',
            'explanation': 'Пояснение к ответу',
            'is_required': 'Обязательный вопрос',
        }
        help_texts = {
            'question_type': 'Выберите тип вопроса: один вариант, несколько вариантов, текстовый ответ или развернутый ответ.',
            'points': 'Сколько баллов студент получит за правильный ответ.',
        }


class TestAnswerForm(forms.ModelForm):
    class Meta:
        model = TestAnswer
        fields = ['answer_text', 'is_correct', 'order']
        widgets = {
            'answer_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите текст ответа...'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }
        labels = {
            'answer_text': 'Текст ответа',
            'is_correct': 'Правильный ответ',
            'order': 'Порядок',
        }


TestAnswerFormSet = forms.inlineformset_factory(
    TestQuestion, 
    TestAnswer, 
    form=TestAnswerForm,
    extra=4,  # Показывать 4 пустых поля для ответов
    can_delete=True,
    min_num=2,  # Минимум 2 варианта ответа
    validate_min=True
)


class PracticeAssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поля имеют значения по умолчанию, делаем их опциональными
        self.fields['time_limit'].required = False
        self.fields['memory_limit'].required = False
        self.fields['max_grade'].required = False
        self.fields['max_attempts'].required = False
        
    class Meta:
        model = PracticeAssignment
        fields = [
            'title', 'description', 'requirements', 'programming_language',
            'starter_code', 'expected_output', 'time_limit', 'memory_limit',
            'max_attempts', 'max_grade', 'deadline', 'require_manual_review', 
            'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название задания'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Опишите, что нужно сделать в этом задании'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Требования к решению'}),
            'programming_language': forms.Select(attrs={'class': 'form-select'}),
            'starter_code': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 10, 'placeholder': 'Начальный код для студентов'}),
            'expected_output': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 5, 'placeholder': 'Пример вывода программы'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 300, 'placeholder': 'Лимит времени в секундах'}),
            'memory_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 64, 'max': 1024, 'placeholder': 'Лимит памяти в МБ'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'max_grade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 1000}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'require_manual_review': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'Название задания',
            'description': 'Описание задания',
            'requirements': 'Требования к решению',
            'programming_language': 'Язык программирования',
            'starter_code': 'Начальный код',
            'expected_output': 'Ожидаемый вывод',
            'time_limit': 'Лимит времени (сек)',
            'memory_limit': 'Лимит памяти (МБ)',
            'max_attempts': 'Максимум попыток',
            'max_grade': 'Максимальная оценка',
            'deadline': 'Дедлайн',
            'require_manual_review': 'Требуется ручная проверка',
            'is_published': 'Опубликовано',
        }
        help_texts = {
            'expected_output': 'Пример вывода, который должен получить студент',
            'max_attempts': 'Сколько раз студент может отправить решение',
            'max_grade': 'Максимальная оценка за задание',
            'deadline': 'Дата и время сдачи задания',
            'require_manual_review': 'Если включено, преподаватель будет проверять задания вручную',
        }


class TestCaseForm(forms.Form):
    """Форма для добавления тестовых случаев"""
    input_data = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Входные данные...'}),
        label='Входные данные',
        required=False
    )
    expected_output = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ожидаемый вывод...'}),
        label='Ожидаемый вывод',
        required=False
    )


class CodeSubmissionForm(forms.ModelForm):
    """Форма отправки кода на проверку"""
    class Meta:
        model = CodeSubmission
        fields = ['code']
        widgets = {
            'code': forms.Textarea(attrs={
                'class': 'form-control font-monospace',
                'rows': 15,
                'placeholder': 'Введите ваш код здесь...'
            })
        }
        labels = {
            'code': 'Код решения'
        }


class SecurityConfigForm(forms.ModelForm):
    """Форма конфигурации безопасности"""
    class Meta:
        model = SecurityConfig
        fields = [
            'programming_language', 'is_enabled', 'compile_command', 'run_command',
            'file_extension', 'max_execution_time', 'max_memory', 'allowed_libraries',
            'forbidden_patterns', 'docker_image', 'security_level'
        ]
        widgets = {
            'programming_language': forms.Select(attrs={'class': 'form-select'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'compile_command': forms.TextInput(attrs={'class': 'form-control'}),
            'run_command': forms.TextInput(attrs={'class': 'form-control'}),
            'file_extension': forms.TextInput(attrs={'class': 'form-control', 'max_length': 10}),
            'max_execution_time': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '300'}),
            'max_memory': forms.NumberInput(attrs={'class': 'form-control', 'min': '64', 'max': '2048'}),
            'allowed_libraries': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '["math", "random", "string"]'}),
            'forbidden_patterns': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': '["import\\\\s+os", "exec\\\\s*("]'}),
            'docker_image': forms.TextInput(attrs={'class': 'form-control'}),
            'security_level': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'programming_language': 'Язык программирования',
            'is_enabled': 'Включен',
            'compile_command': 'Команда компиляции',
            'run_command': 'Команда запуска',
            'file_extension': 'Расширение файла',
            'max_execution_time': 'Макс. время выполнения (сек)',
            'max_memory': 'Макс. память (МБ)',
            'allowed_libraries': 'Разрешенные библиотеки',
            'forbidden_patterns': 'Запрещенные паттерны',
            'docker_image': 'Docker образ',
            'security_level': 'Уровень безопасности',
        }
        help_texts = {
            'compile_command': 'Используйте {file} для имени файла, {filename} для имени без расширения',
            'run_command': 'Используйте {file} для имени файла, {filename} для имени без расширения',
            'allowed_libraries': 'JSON массив разрешенных библиотек',
            'forbidden_patterns': 'JSON массив регулярных выражений',
        }
