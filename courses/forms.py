from django import forms
from .models import CourseReview


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
