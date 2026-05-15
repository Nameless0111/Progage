from django.shortcuts import render
from django.db.models import Count
from courses.models import Course

def home_view(request):
    # Получаем все опубликованные курсы
    all_courses = Course.objects.filter(is_published=True).select_related('instructor', 'category')
        
    # Получаем популярные курсы
    popular_courses = all_courses.annotate(
        like_count=Count('likes')
    ).order_by('-like_count')[:8]
    
    context = {
        'current_year': 2026,
        'users_count': 1000,
        'courses_count': 50,
        'instructors_count': 25,
        'certificates_count': 500,
        'popular_courses': popular_courses,
    }
    return render(request, 'index.html', context)
